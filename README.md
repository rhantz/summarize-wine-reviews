# summarize-wine-reviews


## Methodology

### Data Loading

I loaded all 17.8M reviews. For cheap summarization cost during the POC, I opted to set a ceiling on how many reviews could be selected for summarization input. I set this value to 50. However, increasing this value could increase the variability of inputs, potentially leading to more nuanced summaries, depending on the capabilities of the selected LLM's context recall capabilities. 

After a quick read of the [paper](http://i.stanford.edu/~julian/pdfs/www13.pdf) written by the compilers of this dataset, I learned that one feature that shapes experience is reviewer expertise. This is particularly true for wine--often an acquired taste. Of course, the paper expands on a detailed model of expertise; I took a simple approach. I ensured that the 50 wine reviews selected as input were sorted by reviewers who first, had given the most reviews, then had the longest tenure on the review site, and finally had the highest rating in their review. I'll explain below that I opted to group by wine variant, therefore the inclusion of a sort by rating not only prioritized rated wines, but also those wines that could be later recommended as a good wine to try in the eventual summary.

### Summarization

Since this task was a proof of concept, I opted to only test one, cheap, model recommended for it's feasibility for summarization tasks: OpenAI's gpt-5-nano. I used a temperatue of 1 and low reasoning effort. Other configurations were not tested, but a more thorough investigation could merit such hyperparameter tuning.

Procedurally, I followed these steps:

**1. Query all wine reviews of a given variant up to the described ceiling.** 
    
For prospective customers, I figured one would first want to view wines broadly by category. Later, diving into specific wines potentially recommended by the summary

**2. Format each review alongside the specific name of the wine being reviewed**

This could potentially allow the Summarizer to generate recommended wines inside its summary.

**3. Fill out the prompt template with the wine variant's name and the desired length of the summary.**

While we don't have user requirements, it's worthwhile to view how the length of a summary appeals visually and in content. I mapped each term "short", "medium", "long" to a value for number of sentences (3, 6, and 9 respectively)

**4. Generate the summary.**

**5. Attach a suffix displaying quantitative insights on the wine's average point rating.**

Depending on user requirements, one may be more keen to understand a wine's intrigue quantitatively. Since these values can be computed deterministically, I attached a simple suffix to the summary expressing the wine's mean rating in the input sample. Though, for dynamic flair, I wrote 4 templated options.

### Evaluation

For the sake of the POC, I chose a quick quantitative method of evaluation to inform on the summarization tool's feasibility over a baseline. 

ROUGE is a (albeit noisy and imperfect) metric that gauges the average inclusion (specifically, recall) of words from documents in the summarized result. 

In my evaluation results below, I compare to a baseline. The baseline is 50 randomly selected reviews formatted identically to the true summarization input. Even if ROUGE is imperfect magnitudinally, we can compare directionally if there is growth as compared to a baseline.

In simpler terms, "Are summaries more likely to include actual content from the relevant reviews than arbitrary words?”


### Results

Our results show that answer to be Yes! (minimally)

```
# across 9 summaries (3 of each length)

Baseline Results (Compared to Randomly Selected Reviews)
ROUGE (unigram) : 0.07897590093367403
ROUGE (bigram) : 0.010805214553601726
ROUGE (Longest Common Subsequence) : 0.039153334893942154

Results (Compared to Exact Reviews Used as Summarization Input)
ROUGE (unigram) : 0.09163329358338704
ROUGE (bigram) : 0.022874030103916747
ROUGE (Longest Common Subsequence) : 0.04543003712456442
```
Above, we can see that compared to a baseline, there are marginal differences in the positive direction! Our summarizer is more likely than chance to include single words, pairs of words, and the longest common subsequence from un-summarized reviews in its final summary.

With the time for additional, more robust qualitative evaluation and checks for accuracy, this POC suggests task feasibility.


#### Summaries

variant: cabernet sauvignon; summary length: short

```
Cabernet Sauvignon as a category runs from tight, oak-forward and youthful to deeply structured, richly fruited and long-armed with age, with many examples showing bold dark fruit, cassis or blackberry and substantial tannin. Aromas frequently include vanilla, cedar, tobacco, graphite, and occasional dill or menthol notes, while the palate ranges from elegant and finely balanced to powerful and party-on-the-front, with oak sometimes overwhelming fruit in younger bottles. Start exploring with Amavi for accessible, plump fruit; Quilceda Creek for long-term aging potential and layered richness; and Betz Family or Leonetti for examples that balance intensity with a refined, rooted structure.

With feedback from 50 experienced wine enthusiasts, the most favored of these wines stand at an average rating of 91.0 points out of 100.
```


variant: Pinot Noir; summary length: medium
```
Pinot Noir, as a category, runs from light, elegant Burgundy-like examples to darker, more expressive New World styles, with acidity and earth-driven notes shaping many bottles. Some entries show restraint and fade toward simplicity or dilution (for example, a 2000 Coche-Dury Bourgogne), while others are bright and aromatic but may lack depth (such as the Sea Smoke Pinot Noir Southing). Value and charm appear in approachable Burgundies like the 2005 Catherine et Claude Maréchal Chorey-les-Beaune, which offer bright red fruits, earth, and balanced structure, and in classic, mature examples from Oregon and California noted for balance, aroma, and food-friendly acidity (Domaine Serene Evenstad Reserve and St. Innocent Shea Vineyard). Several standout wines emphasize balance, complexity, and finish, including the 2000 Domaine de la Romanée-Conti La Tâche, the 1985 Rapet Pére et Fils Corton-Perrieres, and the 1990 Emmanuel Rouget Échezeaux, which show depth and long potential with air and time. For quick starters, consider exploring La Tâche, A.F. Gros Richebourg, or a well-aged Domaine Jean Garaudet Pommard to appreciate Pinot’s range of structure, terroir expression, and aging potential. If you’re seeking approachable, food-friendly picks, look to vibrant Chorey-les-Beaune or Savigny-lès-Beaune 1er Cru selections like Nicolas Potel or Chanson Père Fils, which deliver expressive fruit with restraint.

Drawing on the opinions of 50 experienced wine lovers, the best of these wines achieve an average rating of 89.0 points out of 100.
```

variant: Sangiovese; summary length: long

```
Sangiovese wines span a broad spectrum of expression, from mineral-driven to lush, fruit-forward examples. 
Common threads include bright cherry characters, leather or tobacco aromatics, and earthy or floral undertones that can deepen with age. 
Tannin and acidity balance vary, with some wines delivering a silky entry and a nuanced, sometimes drying finish, while others show athletic structure that ages well. 
Oak influence ranges from subtle to pronounced, and in a few bottles it can overwhelm the fruit or mask other complexities. 
Strong, approachable options to start with include Fattoria di Fèlsina Berardenga Chianti Classico Riserva for its aromatic depth and aging potential, and Castello dei Rampolla Chianti Classico Riserva for vibrant acidity and classic profile. 
Notable standouts are 1999 Podere Ciona Chianti Classico Riserva with saddle leather and black cherry, and 1988 Castello dei Rampolla Chianti Classico Riserva offering bright cherries, leather, and tar with floral lift. 
Brunello expressions such as Castello Banfi, Uccelliera, and Poggio Scalette Il Carbonaione reveal depth, spice, and aging potential, though occasional bottles show flaws or oxidation. 
For earlier-drinking, fruit-forward examples, Pride Mountain Sangiovese and 2004 Kuleto Estate Sangiovese deliver peppery notes, pine, and bright red fruit with medium bodies. 
To guide a starting point, consider Fèlsina Berardenga Chianti Classico Riserva (1999 or 2001) or Isole e Olena Cepparello for refined Sangiovese profiles, and Castello Banfi Brunello for a more robust, cellar-worthy experience.

With feedback from 50 experienced wine enthusiasts, the most favored of these wines stand at an average rating of 89.0 points out of 100.
```

variant: Red Bordeaux Blend; summary length: short

```
Red Bordeaux Blend: A broad spectrum of bottle age and terroir shows these wines delivering structure, layered fruit, and the potential for long aging, with many examples offering refined tannins and a velvety mouthfeel when given time. Common threads include aromas of cassis, cedar, tobacco, leather, and earthy graphite, often evolving with decanting to reveal richer fruit and a smoky, spicy backbone, while some bottles remain more firm or rustic in youth. Start exploring with Lynch-Bages for approachable early charm that can age, Montrose for powerful, long-lived profiles, and Léoville Barton for classic, refined Bordeaux character that gains complexity with patience.

Drawing on the opinions of 50 experienced wine lovers, the best of these wines achieve an average rating of 91.0 points out of 100.
```

variant: Roussanne; summary length: medium

```
Roussanne wines present a wide spectrum from bright, floral, mineral styles to richer, oaky, and sometimes hot examples. Many bottles showcase delicate aromatics like honeysuckle, lemon, jasmine, and stone fruit, often with a a clean, crisp acidity and, in stronger examples, an oily or creamy texture. Critics frequently note heat or oak as a drawback, with some wines showing pronounced vanilla, butter, or toast and others aging into more integrated, balanced profiles as they mature. For starters, try Tablas Creek Roussanne for lively honeysuckle and citrus, Alban Estate Roussanne for a richer, buttery edge, or Beaucastel Vieilles Vignes for a complex, age-worthy example with honeyed depth. Several days of aeration or aging seem to help the more oak-forward or high-alcohol bottlings relax and show their best side. Overall, expect a mix of fragrant, fruit-forward profiles and others that lean savory, mineral, or waxy, with finish length ranging from crisp and bright to long and lush.

With feedback from 50 experienced wine enthusiasts, the most favored of these wines stand at an average rating of 90.0 points out of 100.
```

variant: Riesling; summary length: long

```
Riesling is the category here, and the set of notes spans petrol, minerality, citrus, and high acidity across ages.  
Several entries—especially Mosel examples—show diesel or petrol notes pairing with citrus, stone fruit, and chalky minerals.  
Many bottles maintain bright acidity and a light to medium body, with some Auslese and Spätlese offering luscious sweetness and long finishes.  
Dönnhoff and Prüm- and Zilliken wines frequently reveal honeyed, waxy aromas that evolve with air.  
A few bottles suffered cork or bottle faults or were described as austere, spritzy, or showing oxidation risk, influencing enjoyment.  
The best performers deliver precise balance: crisp citrus, slatey minerality, and vibrant acidity that supports the fruit.  
Some entries highlight ageability, with petrol, honey, and mineral complexity balancing sweetness in late-ripening Rieslings.  
Values range from approachable Kabinett and dry expressions to profound Auslese that can be long-lived, with examples like Erdener Treppchen and Eroica cited as reference points.  
For starters, consider Dönnhoff Schloßböckelheimer Felsenberg Spätlese, Zind-Humbrecht Brand, or Robert Weil Kabinett as accessible picks.

Based on the thoughts of 50 experienced wine lovers, the best of these wines hold an average rating of 90.0 points out of 100.
```

variant: Port Blend; summary length: short

```
Port Blend: Reviewers describe a wide range of outcomes across the category, from rich, fruit-forward vintage ports with deep sweetness and noticeable alcohol to more delicate, aged bottlings showing spice, nut and caramel notes. Many suggest that some examples drink well now with good balance and show potential for development, while others suffer from overripe or hot finishes, cork issues, or a lack of acidity and structure. For starting points, consider accessible options like 1991 Fonseca Porto Vintage or 2000 Fonseca Porto Vintage for youthful vigor, 1970 Dow Porto Vintage for precise, restrained complexity, and 1985 Offley Boa Vista Porto Vintage for a balanced, mid-bodied example with integrated tannins.

Based on the thoughts of 50 experienced wine lovers, the best of these wines hold an average rating of 90.0 points out of 100.
```

variant: Chardonnay; summary length: medium

```
Chardonnay as a category showcases a broad spectrum from bright, mineral-laden Chablis to richly oaked, buttery Burgundies and lush California styles. Many tasters highlight vibrant citrus notes—lemons, pears, green apples—and a pronounced mineral or chalky backbone, especially in Chablis and Puligny wines. Oak influence ranges from barely-there to boldly toasted, with descriptors like butter, vanilla, and toast appearing alongside fresh fruit and sometimes a creamy texture. Several bottles display great aging potential, gaining complexity and weight with time, while others are praised for their immediate balance and drinkability, particularly when the finish is long and clean. Standout names to start with include Meursault 1er Cru Charmes, Puligny-Montrachet 1er Cru Clos de la Garenne (and other 1er Crus), Chablis Grand Cru and Chablis Vaillons, as well as acclaimed California examples such as Shafer Red Shoulder Ranch, Aubert Ritchie Vineyard, and Kistler Durell-style bottles. Overall, expect a spectrum of styles, but a common thread of bright acidity, expressive fruit, and nuanced mineral or flinty character runs through many top examples.

Based on the thoughts of 50 experienced wine lovers, the best of these wines hold an average rating of 90.0 points out of 100.
```

variant: Merlot; summary length: long

```
Merlot wines offer a broad spectrum, from plush fruit-driven styles to structured, age-worthy bottles, as reflected by the varied notes across these examples. 
Many entries highlight dark fruit such as blackberry, plum, and cherry, often accompanied by chocolate or cocoa and occasional hints of spice or leather. 
Oak influence ranges from well-integrated, balanced profiles to aggressively toasted or “toasty” finishes that can feel dominant in youth. 
Tannin structure also runs the gamut, with some bottles presenting smooth, refined tannins and others showing firmer, grippier textures that benefit from time. 
Several notes praise remarkable balance and long finishes, while a few bottles are described as polished now but potentially aging to reveal more complexity. 
A handful of bottles are described as underwhelming or flawed (cork issues, heavy oak, or muted aromas), reminding readers that Merlot quality can vary bottle to bottle. 
Notable examples to explore include Pride Mountain Merlot for its evolving nose and tannic backbone, Leonetti for its fruit-forward depth, and Canoe Ridge for balance and a distinct earthiness. 
Other consistently praised bottles include Souverain’s reserve-style profiles, Duckhorn Three Palms for elegant spice and leather, and Castlegiocondo Lamaione for aging potential in a Tuscan classic. 
For a starting point, consider the 2002 Pride Mountain Merlot, 1999 Behrens & Hitchcock Las Amigas, or the 1999 Arietta Merlot as representative samples of this versatile category.

Drawing on the opinions of 50 experienced wine lovers, the best of these wines achieve an average rating of 90.0 points out of 100.
```

### Discussion

The fidelity of the POC appears strong at this initial glance. We can see a good sense of instruction following in summary length as well as in each summary's inclusion of recommended wines. Additionally, each summary has a very decadent tone, using lots of descriptive terms as was present in many of the reviews in our dataset.

Although, we see a lot of noticeably common phrases: "as a category", "broad/wide spectrum" to name a few. This can be annoying. And, without the eye of an expert or the time to build out an automatic evaluation paradigm, it can be hard to gauge the accuracy of descriptions.

### Proposed Next Steps
1. Collect user requirements from the client.
2. Leverage user requirements to build out an evaluation protocol that targets these goals.
3. Determine if Subject Matter Experts or Labeling Projects will be needed to ensure success.
4. Test configurations of various models, model parameters, and prompt instructions. Consider if a dynamically constructed summary from a JSON style Structured Output is more reliable for user needs.
5. If simple prompting is not sufficient to achieve desired summarization form, consider fine-tuning. Always evaluate at each stage to ensure accuracy.
