import numpy as np
import pandas as pd
import html

from typing import Any
from pydantic import BaseModel
from enum import Enum
from openai import OpenAI
import random
client = OpenAI(api_key=)


PROMPT_TEMPLATE = """You are an expert sommelier, wine-reviewer, and copy-writer.
 You have deep empathy in understanding the nuances of brief individual wine reviews and excel at distilling user reviews into a single coherent, easy-to-understand, summary that respects all user viewpoints and experiences for a given wine or generic category of wine. 
 Recently, a large online retailer has employed your wine review summarization services to help them present concise but informative summary reviews that make it easier for prospective customers to choose a wine to purchase.
 
 In the next message, they will provide you with a list of textual customer reviews about the {group_input}: {group_name}. 
 
 Your task is to write a concise, informative summary review that leverages the key points from all user reviews.
 
Ensure that your summary:
 - Captures the most common adjectives, themes, praises and criticisms from the provided reviews.
 - Delivers critical aspect and negative sentiments of reviews professionally and without malice.
 - Does not aim to persuade or dissuade, but rather aims to inform.
 - Highlights taste notes, aromas, body, and any unique qualities mentioned.
 - Avoids copying any single review verbatim.
 - Is exactly {num_sentences} long.
 - Does not mention the word "reviews". Simply describe the wine as if you, yourself are reviewing it, pulling details only from that of the reviews you are provided.
 - Mentions the wine category or name in full in the very first sentence of the summary.
"""

class DataLoader():

    def __init__(self):
        self.file_path = "cellartracker.txt"
        self.df_ratings = self._load_df_ratings()
        self.df_users = self._load_df_users()

    @staticmethod
    def _preprocess_df_ratings(df: pd.DataFrame) -> pd.DataFrame: # TODO drop before 2003
        for col in ["wineId", "userId", "year", "time", "points"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    def _load_df_ratings(self) -> pd.DataFrame:
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f: # TODO check back here
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

    def query_customer_reviews(self, variant: str = None, name: str = None, max_per_variant_per_user: int = 1, max_num_reviews: int = 50) -> pd.DataFrame:
        df = self.df_ratings[
            (self.df_ratings['variant'] == variant) if variant
            else (self.df_ratings['name'] == name)
        ]
        df = df.merge(self.df_users, on="userId", how="left")

        df = df.sort_values( # sort by user experience reviewing
                by=['num_reviews', 'weeks_as_reviewer'],
                ascending=[False, False]
            )

        if variant is not None:
            df = df.groupby('userId').head(n=max_per_variant_per_user)

        return df[['userId', 'points', 'text']].head(max_num_reviews)


class SummaryLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class SummarizerRequest(BaseModel):
    group_input: str
    group_name: str
    summary_length: SummaryLength
    customer_reviews: Any


class Summarizer:
    def __init__(self, request: SummarizerRequest):
        self.group_input=request.group_input
        self.group_name=request.group_name
        self.summary_length=request.summary_length
        self.customer_reviews=request.customer_reviews

    def summarize(self):
        return self._generate_response() + "\n\n" + self._add_quantitative_insights()

    def _generate_response(self):
        instructions=self._load_instructions()
        input=self._format_customer_reviews()
        response = client.responses.create(
            model="gpt-5-nano",
            reasoning={"effort": "low"},
            instructions=instructions,
            input=input,
            temperature=1
        )
        return response.output[1].content[0].text

    def _load_instructions(self) -> str:
        return self._format_prompt(prompt_template=PROMPT_TEMPLATE)

    def _set_num_sentences(self) -> int:
        if self.summary_length == SummaryLength.SHORT:
            return 3
        elif self.summary_length == SummaryLength.MEDIUM:
            return 6
        elif self.summary_length == SummaryLength.LONG:
            return 9
        else:
            raise ValueError("Invalid summary length")

    def _format_customer_reviews(self) -> str:
        return "\n\n".join([
            review for review in self.customer_reviews["text"].tolist()
        ])

    def _format_prompt(self, prompt_template: str) -> str:
        return prompt_template.format(
            group_input=self.group_input,
            group_name=self.group_name,
            num_sentences=self._set_num_sentences(),
        )

    def _add_quantitative_insights(self) -> str:
        num_reviews = len(self.customer_reviews)
        average_points = round(self.customer_reviews["points"].mean(), 0) # TODO median?
        suffix_templates = [
            f"Based on the thoughts of {num_reviews} experienced wine lovers, the wine holds an average rating of {average_points} points out of 100.",
            f"Across the tastes of {num_reviews} experienced wine enthusiasts, the wine earns an average rating of {average_points} points out of 100.",
            f"Drawing on the opinions of {num_reviews} experienced wine lovers, the wine achieves an average rating of {average_points} points out of 100."
            f"With feedback from {num_reviews} experienced wine enthusiasts, this wine stands at an average rating of {average_points} points out of 100.",
        ]
        return random.choice(suffix_templates).format(
            num_reviews=num_reviews,
            average_points=average_points,
        )


if __name__ == '__main__':

    data_loader = DataLoader()

    variant = "Cabernet Sauvignon"
    name = None
    summary_length = SummaryLength.MEDIUM

    summarizer = Summarizer(
        request=SummarizerRequest(
            group_input="wine category" if variant else "wine",
            group_name=variant if variant else name,
            summary_length=summary_length,
            customer_reviews=data_loader.query_customer_reviews(
                variant=variant,
            ),
        )
    )
    summary = summarizer.summarize()

    print(summary)


