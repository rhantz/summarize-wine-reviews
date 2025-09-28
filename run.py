import numpy as np
import pandas as pd
import html

from typing import Any
from pydantic import BaseModel
from enum import Enum
from openai import OpenAI
import random
from loguru import logger
import evaluate

import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


PROMPT_TEMPLATE = """You are an expert sommelier, wine-reviewer, and copy-writer.
 You have deep empathy in understanding the nuances of brief individual wine reviews and excel at distilling user reviews into a single coherent, easy-to-understand, summary that respects all user viewpoints and experiences for a given category of wine. 
 Recently, a large online retailer has employed your wine review summarization services to help them present concise but informative summary reviews that make it easier for prospective customers to choose a wine to purchase.
 
 In the next message, they will provide you with a list of textual customer reviews about the wine category: {variant}.
 
 Each review will be presented on a new line in the form:
 <wine name>: <review> 
 
 Your task is to write a concise, informative summary review that leverages the key points from all user reviews.
 
Ensure that your summary:
 - Captures the most common adjectives, themes, praises and criticisms from the provided reviews.
 - Delivers any critical aspects and negative sentiments of reviews professionally and without malice.
 - Does not aim to persuade or dissuade, but rather aims to inform.
 - Highlights taste notes, aromas, body, and any unique qualities mentioned.
 - Avoids copying any single review verbatim.
 - Is exactly {num_sentences} sentences long.
 - Does not mention the word "reviews". Simply describes the wine as if you, yourself are reviewing it, pulling details only from that of the reviews you are provided.
 - Mentions the wine category in full in the very first sentence of the summary.
 - Suggests specific wine names where relevant to help prospective customers find a place to start.
"""

class DataLoader:
    """Handles loading, preprocessing, and querying wine review data."""

    def __init__(self):
        """Initialize the DataLoader by loading ratings, users, and baseline summary."""
        self.file_path = "cellartracker.txt"
        self.df_ratings = self._load_df_ratings()
        self.df_users = self._load_df_users()

        self.baseline_reference = self._get_baseline_reference()

    @staticmethod
    def _preprocess_df_ratings(df: pd.DataFrame) -> pd.DataFrame:
        """Convert numeric columns and timestamps in the ratings DataFrame.

        Args:
            df (pd.DataFrame): Raw ratings DataFrame.

        Returns:
            pd.DataFrame: Preprocessed ratings DataFrame.
        """
        for col in ["wineId", "userId", "year", "time", "points"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    def _load_df_ratings(self) -> pd.DataFrame:
        """Load and parse wine ratings from the source file.

        Returns:
            pd.DataFrame: Ratings DataFrame.
        """
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            rating_records = [
                {
                    key.split("/")[-1]: value
                    for key, value in (key_value_pair.split(": ", 1)
                    for key_value_pair in record.split("\n"))
                }
                for record in html.unescape(f.read()).split("\n\n")
            ]
        return self._preprocess_df_ratings(df=pd.DataFrame(rating_records))

    def _load_df_users(self):
        """Aggregate user-level review stats from ratings DataFrame.

        Returns:
            pd.DataFrame: Users DataFrame with review counts and weeks active.
        """
        df_users = (
            self.df_ratings[["userId", "time"]].groupby('userId')
            .agg(
                num_reviews=('userId', 'count'),
                first_review=('time', 'min'),
                last_review=('time', 'max')
            )
            .reset_index()
        )
        df_users['weeks_as_reviewer'] = (
                (df_users['last_review'] - df_users['first_review']) / np.timedelta64(1, 'W')
        ).round(1)
        return df_users[['userId', 'num_reviews', 'weeks_as_reviewer']].sort_values(
            by=['num_reviews', 'weeks_as_reviewer'],
            ascending=[False, False]
        )

    def query_customer_reviews(self, variant: str, max_num_reviews: int = 50) -> pd.DataFrame:
        """Retrieve a sample of customer reviews for a given wine variant.

        Args:
            variant (str): Wine variant to query.
            max_num_reviews (int): Maximum number of reviews to return. (To help keep input token cost low for POC)

        Returns:
            pd.DataFrame: Filtered and sampled reviews DataFrame.
        """
        df = self.df_ratings[self.df_ratings['variant'].str.lower() == variant.lower()]
        df = df.merge(self.df_users, on="userId", how="left")
        df = df.sort_values( # sort by user experience reviewing then rating
                by=['num_reviews', 'weeks_as_reviewer', 'points'],
                ascending=[False, False, False]
            )
        df = df.groupby('userId').sample(n=1, random_state=7) # 1 review per user to aid in diversity of inputs
        return df[['userId', 'points', 'text', 'name']].head(max_num_reviews)

    def _get_baseline_reference(self) -> str:
        """Generate a baseline reference from random sample of reviews.

        Returns:
            str: Concatenated string of random wine reviews.
        """
        df_sample = self.df_ratings.sample(n=50, random_state=7)
        return "\n\n".join([ # random 50 reviews
            f"{review['name']}: {review['text']}" for _, review in df_sample.iterrows()
        ])


class SummaryLength(str, Enum):
    """Enumeration of allowed summary lengths."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class SummarizerRequest(BaseModel):
    """Request schema for Summarizer inputs."""
    variant: str
    summary_length: SummaryLength
    customer_reviews: Any


class Summarizer:
    """Generates wine review summaries using OpenAI models."""
    def __init__(self, request: SummarizerRequest):
        """Initialize Summarizer with request data."""
        self.variant = request.variant
        self.summary_length=request.summary_length
        self.customer_reviews=request.customer_reviews

        self.instructions = self._load_instructions()
        self.user_input = self._format_customer_reviews()

    def summarize(self):
        """Generate a summary with quantitative insights.

        Returns:
            str: Final summary including average rating context.
        """
        return self._generate_response() + "\n\n" + self._add_quantitative_insights()

    def _generate_response(self):
        """Call the OpenAI model to generate a summary.

        Returns:
            str: Model-generated summary text.
        """
        instructions=self.instructions
        user_input=self.user_input
        response = client.responses.create(
            model="gpt-5-nano",
            reasoning={"effort": "low"},
            instructions=instructions,
            input=user_input,
            temperature=1
        )
        return response.output[1].content[0].text

    def _load_instructions(self) -> str:
        """Format and load summarization prompt instructions.

        Returns:
            str: Fully formatted instruction string.
        """
        return self._format_prompt(prompt_template=PROMPT_TEMPLATE)

    def _set_num_sentences(self) -> int:
        """Determine the number of sentences based on summary length.

        Returns:
            int: Number of sentences in summary.

        Raises:
            ValueError: If summary length is invalid.
        """
        if self.summary_length == SummaryLength.SHORT:
            return 3
        elif self.summary_length == SummaryLength.MEDIUM:
            return 6
        elif self.summary_length == SummaryLength.LONG:
            return 9
        else:
            raise ValueError("Invalid summary length")

    def _format_customer_reviews(self) -> str:
        """Format customer reviews into string input for the model.

        Returns:
            str: Formatted string of reviews.
        """
        return "\n\n".join([
            f"{review['name']}: {review['text']}" for _, review in self.customer_reviews.iterrows()
        ])

    def _format_prompt(self, prompt_template: str) -> str:
        """Fill template with variant and sentence count.

        Args:
            prompt_template (str): Prompt template string.

        Returns:
            str: Formatted prompt ready for the model.
        """
        return prompt_template.format(
            variant=self.variant,
            num_sentences=self._set_num_sentences(),
        )

    def _add_quantitative_insights(self) -> str:
        """Append average rating context to the summary.

        Returns:
            str: Quantitative insights text.
        """
        num_reviews = len(self.customer_reviews)
        average_points = round(self.customer_reviews["points"].mean(), 0)
        suffix_templates = [
            f"Based on the thoughts of {num_reviews} experienced wine lovers, the best of these wines hold an average rating of {average_points} points out of 100.",
            f"Across the tastes of {num_reviews} experienced wine enthusiasts, the most favored of these wines earn an average rating of {average_points} points out of 100.",
            f"Drawing on the opinions of {num_reviews} experienced wine lovers, the best of these wines achieve an average rating of {average_points} points out of 100.",
            f"With feedback from {num_reviews} experienced wine enthusiasts, the most favored of these wines stand at an average rating of {average_points} points out of 100.",
        ]
        return random.choice(suffix_templates).format( # randomly select a template
            num_reviews=num_reviews,
            average_points=average_points,
        )


if __name__ == '__main__':

    logger.info("Loading data...")
    data_loader = DataLoader()

    references = []
    predictions = []

    while True:
        # Prompt user for wine variant and summary length
        variant = input("Enter wine variant to summarize: ").strip()
        summary_length = SummaryLength(input("Enter summary length (short, medium, long): ").strip().lower())

        # Build summarizer
        summarizer = Summarizer(
            request=SummarizerRequest(
                variant=variant,
                summary_length=summary_length,
                customer_reviews=data_loader.query_customer_reviews(
                    variant=variant,
                ),
            )
        )

        # Generate and print summary
        logger.info("Summarizing...")
        summary = summarizer.summarize()
        print("\n--- SUMMARY ---")
        print(summary)
        print("---------------\n")

        references.append(summarizer.user_input)
        predictions.append(summary)

        # Ask if user wants another summary
        again = input("Generate another summary? (y/n): ").strip().lower()
        if again not in ('y', 'yes'):
            print("Exiting.")
            break

    # Evaluate ROUGE score (average recall of n-grams)
    logger.info("Evaluating...")
    rouge = evaluate.load('rouge')

    baseline_results = rouge.compute(predictions=predictions, references=[data_loader.baseline_reference] * len(predictions))
    print("\n\nBaseline Results (Compared to Randomly Selected Reviews)")

    print(f"ROUGE (unigram) : {baseline_results['rouge1']}")
    print(f"ROUGE (bigram) : {baseline_results['rouge2']}")
    print(f"ROUGE (Longest Common Subsequence) : {baseline_results['rougeL']}")

    results = rouge.compute(predictions=predictions, references=references)
    print("\n\nResults (Compared to Exact Reviews Used as Summarization Input)")

    print(f"ROUGE (unigram) : {results['rouge1']}")
    print(f"ROUGE (bigram) : {results['rouge2']}")
    print(f"ROUGE (Longest Common Subsequence) : {results['rougeL']}")




