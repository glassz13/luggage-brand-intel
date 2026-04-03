"""
analyze.py
Single pipeline: BERT sentiment → aspect extraction → TF-IDF themes →
anomaly detection → trust signals → value for money → brand_summary.json

Run: python analyze/analyze.py
"""

import os
import re
import json
import numpy as np
import pandas as pd
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

# ── Paths ─────────────────────────────────────────────────────────────────────
REVIEWS_INPUT  = "data/clean/reviews_clean.csv"
PRODUCTS_INPUT = "data/clean/products_clean.csv"
OUTPUT         = "data/analyzed/brand_summary.json"
os.makedirs("data/analyzed", exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
MODEL            = "nlptown/bert-base-multilingual-uncased-sentiment"
BATCH_SIZE       = 16
MAX_TOKENS       = 512
TOP_N_THEMES     = 10
MIN_REVIEWS      = 3

STAR_TO_POLARITY = {1: -1.0, 2: -0.5, 3: 0.0, 4: 0.5, 5: 1.0}

PRICE_BANDS = {
    "budget":  (0,    2000),
    "mid":     (2000, 5000),
    "premium": (5000, float("inf")),
}

ASPECTS = {
    "wheels":     ["wheel", "wheels", "rolling", "rolls", "spinner",
                   "rotate", "rotation", "wobble", "smooth roll", "dual wheel"],
    "zipper":     ["zipper", "zip", "zippers", "zips", "lock", "locks",
                   "locking", "tsa", "closure"],
    "handle":     ["handle", "handles", "grip", "trolley handle",
                   "pull", "retract", "telescopic"],
    "material":   ["material", "plastic", "polycarbonate", "polypropylene",
                   "fabric", "shell", "hard case", "soft case", "finish",
                   "texture", "surface"],
    "durability": ["durable", "durability", "sturdy", "strong", "broke",
                   "broken", "crack", "cracked", "scratch", "scratches",
                   "build quality", "build", "lasting", "wear", "tear"],
    "size":       ["size", "spacious", "capacity", "fits", "cabin",
                   "overhead", "compartment", "small", "large", "medium",
                   "big", "compact", "roomy"],
    "price":      ["price", "value", "worth", "expensive", "cheap",
                   "affordable", "money", "cost", "budget", "overpriced",
                   "value for money"],
}

THEME_STOPWORDS = [
    "product", "bag", "luggage", "suitcase", "trolley", "bought",
    "purchase", "ordered", "amazon", "delivery", "order", "received",
    "good", "nice", "bad", "okay", "ok", "just", "also", "very",
    "really", "bit", "little", "like", "use", "used", "using", "one",
    "two", "get", "got", "great", "best", "worst", "better", "item",
    "brand", "overall", "quality"
]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def split_sentences(text):
    sentences = re.split(r"[.!?\n]+", str(text))
    return [s.strip() for s in sentences if len(s.strip()) > 8]

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_tfidf_themes(texts, top_n=TOP_N_THEMES):
    if len(texts) < MIN_REVIEWS:
        return []
    cleaned = [clean_text(t) for t in texts]
    vectorizer = TfidfVectorizer(
        ngram_range  = (1, 3),
        stop_words   = "english",
        max_features = 500,
    )
    try:
        matrix = vectorizer.fit_transform(cleaned)
    except ValueError:
        return []
    scores  = np.asarray(matrix.sum(axis=0)).flatten()
    vocab   = vectorizer.get_feature_names_out()
    ranked  = sorted(zip(vocab, scores), key=lambda x: x[1], reverse=True)
    return [
        phrase for phrase, _ in ranked
        if phrase not in THEME_STOPWORDS
        and len(phrase) > 3
        and not phrase.isdigit()
    ][:top_n]

def get_examples(texts, keywords, n=3):
    examples = []
    for text in texts:
        for s in split_sentences(text):
            if len(s) > 15 and any(kw in s.lower() for kw in keywords):
                examples.append(s)
                if len(examples) >= n:
                    return examples
    return examples

def weighted_mean(polarities, scores):
    """Confidence-weighted average polarity."""
    if not polarities:
        return None
    pol = np.array(polarities)
    wts = np.array(scores)
    return round(float(np.average(pol, weights=wts)), 4)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 1 — Loading data")
print("="*60)

reviews  = pd.read_csv(REVIEWS_INPUT)
products = pd.read_csv(PRODUCTS_INPUT)

before = len(reviews)
reviews = reviews[
    reviews["review_body"].notna() &
    (reviews["review_body"].str.strip() != "")
]
print(f"Reviews loaded: {len(reviews)} (dropped {before - len(reviews)} empty)")
print(f"Products loaded: {len(products)}")
print(f"Brands: {reviews['brand'].unique().tolist()}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — BERT SENTIMENT PER REVIEW (confidence weighted)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 2 — BERT sentiment per review")
print("="*60)

sentiment_pipe = pipeline(
    task       = "text-classification",
    model      = MODEL,
    truncation = True,
    max_length = MAX_TOKENS,
    device     = -1,
)

texts   = reviews["review_body"].str[:2048].tolist()
results = []

for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Review sentiment"):
    results.extend(sentiment_pipe(texts[i : i + BATCH_SIZE]))

reviews["sentiment_label"]    = [r["label"] for r in results]
reviews["sentiment_score"]    = [round(r["score"], 4) for r in results]
reviews["star_prediction"]    = reviews["sentiment_label"].str.extract(r"(\d)").astype(int)
reviews["sentiment_polarity"] = reviews["star_prediction"].map(STAR_TO_POLARITY)

# Weighted polarity — confidence as weight
# High confidence negative counts more than uncertain negative
reviews["weighted_polarity"] = (
    reviews["sentiment_polarity"] * reviews["sentiment_score"]
).round(4)

print(f"\nStar prediction distribution:\n{reviews['star_prediction'].value_counts().sort_index()}")
print(f"\nPer-brand weighted polarity:")
print(
    reviews.groupby("brand")["weighted_polarity"]
    .mean().round(3)
    .sort_values(ascending=False)
)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — ASPECT EXTRACTION (sentence level BERT, confidence weighted)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 3 — Aspect extraction")
print("="*60)

# Collect all matched sentences across all reviews
records = []
for idx, row in reviews.iterrows():
    sentences = split_sentences(row["review_body"])
    for asp, keywords in ASPECTS.items():
        matched = [
            s for s in sentences
            if any(kw.lower() in s.lower() for kw in keywords)
        ]
        for s in matched:
            records.append({
                "review_idx": idx,
                "brand":      row["brand"],
                "aspect":     asp,
                "sentence":   s,
            })

records_df = pd.DataFrame(records)
print(f"Found {len(records_df)} aspect-sentence matches")
print(f"Breakdown: {records_df['aspect'].value_counts().to_dict()}")

# Batch BERT on matched sentences only
asp_texts = records_df["sentence"].tolist()
asp_results = []

for i in tqdm(range(0, len(asp_texts), BATCH_SIZE), desc="Aspect sentiment"):
    asp_results.extend(sentiment_pipe(asp_texts[i : i + BATCH_SIZE]))

records_df["asp_label"]    = [r["label"] for r in asp_results]
records_df["asp_score"]    = [round(r["score"], 4) for r in asp_results]
records_df["asp_stars"]    = records_df["asp_label"].str.extract(r"(\d)").astype(int)
records_df["asp_polarity"] = records_df["asp_stars"].map(STAR_TO_POLARITY)

# Confidence weighted aspect polarity per review per aspect
def wavg(group):
    return np.average(group["asp_polarity"], weights=group["asp_score"])

aspect_pivot = (
    records_df
    .groupby(["review_idx", "aspect"])
    .apply(wavg,include_groups=False)
    .unstack("aspect")
    .round(4)
)
aspect_pivot.columns = [f"aspect_{c}" for c in aspect_pivot.columns]
reviews = reviews.join(aspect_pivot)

for asp in ASPECTS:
    col = f"aspect_{asp}"
    if col not in reviews.columns:
        reviews[col] = np.nan

print("\nAspect coverage (% reviews mentioning each aspect):")
for asp in ASPECTS:
    col     = f"aspect_{asp}"
    covered = reviews[col].notna().sum()
    print(f"  {asp:<12} {covered:>4} / {len(reviews)}  ({round(covered/len(reviews)*100,1)}%)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — TF-IDF THEMES
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 4 — TF-IDF themes per brand")
print("="*60)

themes_by_brand = {}
for brand in reviews["brand"].unique():
    bdf      = reviews[reviews["brand"] == brand]
    pos_texts = bdf[bdf["star_prediction"] >= 4]["review_body"].dropna().tolist()
    neg_texts = bdf[bdf["star_prediction"] <= 2]["review_body"].dropna().tolist()

    top_praise     = extract_tfidf_themes(pos_texts)
    top_complaints = extract_tfidf_themes(neg_texts)

    themes_by_brand[brand] = {
        "top_praise":          top_praise,
        "top_complaints":      top_complaints,
        "praise_examples":     get_examples(pos_texts, top_praise[:3]),
        "complaint_examples":  get_examples(neg_texts, top_complaints[:3]),
    }
    print(f"  {brand}: praise={top_praise[:3]} | complaints={top_complaints[:3]}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — ANOMALY DETECTION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 5 — Anomaly detection")
print("="*60)

anomalies_by_brand = {}
for brand in reviews["brand"].unique():
    bdf      = reviews[reviews["brand"] == brand]
    anomalies = []

    # Anomaly 1: High star rating but BERT says negative
    # Customer gave 4-5 stars but review text is negative (star_prediction <= 2)
    hidden = bdf[
        (bdf["star_rating"] >= 4) &
        (bdf["star_prediction"] <= 2)
    ]
    if len(hidden) > 0:
        pct = round(len(hidden) / len(bdf) * 100, 1)
        anomalies.append({
            "type":        "hidden_dissatisfaction",
            "description": f"{len(hidden)} reviews ({pct}%) gave high stars but text is negative",
            "severity":    "high" if pct > 20 else "medium",
            "examples":    hidden["review_body"].head(2).tolist(),
        })

    # Anomaly 2: Specific aspect very negative despite good overall sentiment
    brand_avg_polarity = bdf["weighted_polarity"].mean()
    for asp in ASPECTS:
        col     = f"aspect_{asp}"
        asp_avg = bdf[col].mean()
        if pd.notna(asp_avg) and asp_avg < -0.3 and brand_avg_polarity > 0:
            anomalies.append({
                "type":        "aspect_anomaly",
                "description": f"Overall sentiment positive ({round(brand_avg_polarity,2)}) but {asp} scores very negative ({round(asp_avg,2)})",
                "severity":    "high" if asp_avg < -0.5 else "medium",
                "aspect":      asp,
            })

    # Anomaly 3: Rating skew — too many 5 stars, suspicious distribution
    five_star_pct = len(bdf[bdf["star_rating"] == 5]) / len(bdf)
    one_star_pct  = len(bdf[bdf["star_rating"] == 1]) / len(bdf)
    if five_star_pct > 0.6 and one_star_pct < 0.05:
        anomalies.append({
            "type":        "rating_skew",
            "description": f"{round(five_star_pct*100,1)}% five-star ratings with only {round(one_star_pct*100,1)}% one-star — possibly inflated",
            "severity":    "medium",
        })

    anomalies_by_brand[brand] = anomalies
    if anomalies:
        print(f"  {brand}: {len(anomalies)} anomalies found")
        for a in anomalies:
            print(f"    [{a['severity'].upper()}] {a['type']}: {a['description']}")
    else:
        print(f"  {brand}: no anomalies")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — REVIEW TRUST SIGNALS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 6 — Review trust signals")
print("="*60)

trust_by_brand = {}
for brand in reviews["brand"].unique():
    bdf    = reviews[reviews["brand"] == brand]
    flags  = {}

    # Trust signal 1: % unverified purchases
    if "verified_purchase" in bdf.columns:
        unverified_pct = round(
            (bdf["verified_purchase"] == False).sum() / len(bdf) * 100, 1
        )
        flags["unverified_purchase_pct"] = unverified_pct
        if unverified_pct > 30:
            flags["unverified_warning"] = f"{unverified_pct}% reviews are unverified purchases"

    # Trust signal 2: suspiciously short positive reviews
    # Very short reviews with high confidence positive — potentially fake
    short_positive = bdf[
        (bdf["review_body"].str.split().str.len() < 5) &
        (bdf["star_prediction"] == 5) &
        (bdf["sentiment_score"] > 0.85)
    ]
    flags["short_positive_count"] = len(short_positive)
    if len(short_positive) > 3:
        flags["short_positive_warning"] = (
            f"{len(short_positive)} suspiciously short high-confidence positive reviews"
        )

    # Trust signal 3: near duplicate review bodies
    # Hash first 50 chars — catches copy-paste reviews
    bdf = bdf.copy()
    bdf["review_prefix"] = bdf["review_body"].str[:50].str.lower().str.strip()
    duplicate_count      = bdf["review_prefix"].duplicated().sum()
    flags["duplicate_review_count"] = int(duplicate_count)
    if duplicate_count > 2:
        flags["duplicate_warning"] = f"{duplicate_count} near-duplicate reviews detected"

    trust_by_brand[brand] = flags
    print(f"  {brand}: {flags}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — VALUE FOR MONEY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 7 — Value for money analysis")
print("="*60)

# Merge reviews with products to get price per review
reviews_with_price = reviews.merge(
    products[["asin", "price", "mrp", "discount_pct"]],
    on   = "asin",
    how  = "left",
)

def get_price_band(price):
    if pd.isna(price):
        return "unknown"
    for band, (low, high) in PRICE_BANDS.items():
        if low <= price < high:
            return band
    return "unknown"

reviews_with_price["price_band"] = reviews_with_price["price"].apply(get_price_band)

vfm_by_brand = {}
for brand in reviews["brand"].unique():
    bdf = reviews_with_price[reviews_with_price["brand"] == brand]

    # Sentiment per price band
    band_sentiment = (
        bdf.groupby("price_band")["weighted_polarity"]
        .mean()
        .round(3)
        .to_dict()
    )

    # Value score: weighted_polarity / normalized_price
    # Higher sentiment at lower price = better value
    avg_price     = bdf["price"].mean()
    avg_sentiment = bdf["weighted_polarity"].mean()

    if pd.notna(avg_price) and avg_price > 0:
        # Normalize price to 0-1 range across all brands later
        vfm_raw = avg_sentiment / (avg_price / 1000)
    else:
        vfm_raw = None

    vfm_by_brand[brand] = {
        "avg_price":          round(avg_price, 2) if pd.notna(avg_price) else None,
        "avg_sentiment":      round(avg_sentiment, 3),
        "band_sentiment":     band_sentiment,
        "vfm_raw_score":      round(vfm_raw, 4) if vfm_raw else None,
    }

# Normalize vfm_raw_score to 0-100 across brands
vfm_scores = [v["vfm_raw_score"] for v in vfm_by_brand.values() if v["vfm_raw_score"]]
if vfm_scores:
    min_vfm = min(vfm_scores)
    max_vfm = max(vfm_scores)
    for brand in vfm_by_brand:
        raw = vfm_by_brand[brand]["vfm_raw_score"]
        if raw and max_vfm != min_vfm:
            vfm_by_brand[brand]["vfm_score_normalized"] = round(
                (raw - min_vfm) / (max_vfm - min_vfm) * 100, 1
            )
        else:
            vfm_by_brand[brand]["vfm_score_normalized"] = 50.0

print("\nValue for money scores (normalized 0-100):")
for brand, data in vfm_by_brand.items():
    print(f"  {brand:<20} vfm={data.get('vfm_score_normalized')} | avg_price=₹{data['avg_price']} | sentiment={data['avg_sentiment']}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — AGGREGATE INTO brand_summary.json
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 8 — Aggregating into brand_summary.json")
print("="*60)

brand_summary = {}

for brand in reviews["brand"].unique():
    bdf  = reviews[reviews["brand"] == brand]
    pdf  = products[products["brand"] == brand]

    # ── Sentiment ──────────────────────────────────────────────────────────
    total          = len(bdf)
    positive_count = len(bdf[bdf["star_prediction"] >= 4])
    negative_count = len(bdf[bdf["star_prediction"] <= 2])
    neutral_count  = len(bdf[bdf["star_prediction"] == 3])

    sentiment = {
        "avg_polarity":          round(bdf["sentiment_polarity"].mean(), 3),
        "avg_weighted_polarity": round(bdf["weighted_polarity"].mean(), 3),
        "positive_pct":          round(positive_count / total * 100, 1),
        "negative_pct":          round(negative_count / total * 100, 1),
        "neutral_pct":           round(neutral_count  / total * 100, 1),
        "total_reviews":         total,
    }

    # ── Pricing ────────────────────────────────────────────────────────────
    pricing = {
        "avg_price":        round(pdf["price"].mean(), 2)        if len(pdf) else None,
        "avg_mrp":          round(pdf["mrp"].mean(), 2)          if len(pdf) else None,
        "avg_discount_pct": round(pdf["discount_pct"].mean(), 1) if len(pdf) else None,
        "min_price":        round(pdf["price"].min(), 2)         if len(pdf) else None,
        "max_price":        round(pdf["price"].max(), 2)         if len(pdf) else None,
        "inflated_mrp_flag": bool(
            pdf["discount_pct"].mean() > 70
        ) if len(pdf) and "discount_pct" in pdf.columns else False,
    }

    # ── Ratings ────────────────────────────────────────────────────────────
    ratings = {
        "avg_star_rating": round(pdf["rating"].mean(), 2)        if len(pdf) else None,
        "total_products":  len(pdf),
        "avg_review_count": round(pdf["review_count"].mean(), 0) if len(pdf) else None,
    }

    # ── Aspects ────────────────────────────────────────────────────────────
    aspects = {}
    for asp in ASPECTS:
        col = f"aspect_{asp}"
        val = bdf[col].mean()
        aspects[asp] = round(float(val), 3) if pd.notna(val) else None

    # ── Assemble ───────────────────────────────────────────────────────────
    brand_summary[brand] = {
        "sentiment":      sentiment,
        "pricing":        pricing,
        "ratings":        ratings,
        "aspects":        aspects,
        "themes":         themes_by_brand.get(brand, {}),
        "anomalies":      anomalies_by_brand.get(brand, []),
        "trust_signals":  trust_by_brand.get(brand, {}),
        "value_for_money": vfm_by_brand.get(brand, {}),
    }

# ── Save ──────────────────────────────────────────────────────────────────────
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(brand_summary, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! Saved to {OUTPUT}")
print("\nFinal brand summary:")
for brand, data in brand_summary.items():
    print(f"\n  {brand}")
    print(f"    sentiment:    {data['sentiment']['avg_weighted_polarity']}")
    print(f"    avg_price:    ₹{data['pricing']['avg_price']}")
    print(f"    avg_rating:   {data['ratings']['avg_star_rating']}")
    print(f"    vfm_score:    {data['value_for_money'].get('vfm_score_normalized')}")
    print(f"    anomalies:    {len(data['anomalies'])}")
    print(f"    top_praise:   {data['themes'].get('top_praise', [])[:3]}")
    print(f"    top_complaints: {data['themes'].get('top_complaints', [])[:3]}")