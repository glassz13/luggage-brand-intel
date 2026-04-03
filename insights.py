"""
5_insights.py
Generates 5 non-obvious competitive insights from brand_summary.json
Pure logic — no API, deterministic, works at any scale.

Output: data/analyzed/insights.json
Run: python analyze/5_insights.py
"""

import json
import os

INPUT  = "data/analyzed/brand_summary.json"
OUTPUT = "data/analyzed/insights.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

brands = list(data.keys())
insights = []

# ── INSIGHT 1: Star Rating vs BERT Sentiment Disconnect ───────────────────────
# Brands where customers rate high but text sentiment is negative
# This is the most non-obvious finding — surface metrics lie
disconnects = []
for brand in brands:
    star  = data[brand]["ratings"]["avg_star_rating"]
    bert  = data[brand]["sentiment"]["avg_weighted_polarity"]
    gap   = round(star - (bert * 5 + 3), 2)  # normalize bert to 1-5 scale
    disconnects.append((brand, star, bert, gap))

disconnects.sort(key=lambda x: x[3], reverse=True)
worst = disconnects[0]
insights.append({
    "id":          1,
    "title":       f"{worst[0]} Has the Biggest Gap Between Stars and Real Sentiment",
    "insight":     (
        f"{worst[0]} has an average star rating of {worst[1]} — respectable on the surface. "
        f"But BERT sentiment analysis of review text gives a weighted polarity of {worst[2]}, "
        f"equivalent to roughly {round(worst[2]*5+3, 1)} on a 5-point scale. "
        f"That's a gap of {worst[3]} points. "
        f"Customers are rating generously but writing negatively — "
        f"a pattern common when buyers feel social pressure to rate high on Amazon India."
    ),
    "implication": (
        f"Star ratings for {worst[0]} are unreliable signals. "
        f"Any competitor benchmarking against {worst[0]}'s star rating is being misled. "
        f"Focus on text sentiment, not stars."
    ),
    "severity":    "high",
})

# ── INSIGHT 2: The Hidden Gem — High Sentiment, Low Price ─────────────────────
# Brand with best value for money that isn't the most reviewed
vfm_ranked = sorted(
    brands,
    key=lambda b: data[b]["value_for_money"].get("vfm_score_normalized", 0),
    reverse=True
)
gem         = vfm_ranked[0]
gem_data    = data[gem]
runner_up   = vfm_ranked[1]

insights.append({
    "id":          2,
    "title":       f"{gem} Is the Hidden Gem — Best Value, Not the Most Visible Brand",
    "insight":     (
        f"{gem} scores {gem_data['value_for_money']['vfm_score_normalized']}/100 on value for money — "
        f"highest across all brands. Average price is ₹{gem_data['value_for_money']['avg_price']} "
        f"with a sentiment polarity of {gem_data['sentiment']['avg_weighted_polarity']}. "
        f"Compare this to {runner_up} at vfm={data[runner_up]['value_for_money']['vfm_score_normalized']}/100. "
        f"{gem_data['sentiment']['total_reviews']} reviews vs "
        f"{data[vfm_ranked[-1]]['sentiment']['total_reviews']} for the most reviewed brand — "
        f"{gem} is flying under the radar."
    ),
    "implication": (
        f"A budget-conscious buyer choosing based on reviews alone will miss {gem}. "
        f"Brands competing in the budget segment should treat {gem} as the benchmark, not {vfm_ranked[-1]}."
    ),
    "severity": "high",
})

# ── INSIGHT 3: Aspect Anomaly — Specific Failure Despite Good Overall ─────────
# Find brand with best overall sentiment but worst single aspect
aspect_anomalies = []
for brand in brands:
    overall = data[brand]["sentiment"]["avg_weighted_polarity"]
    aspects = data[brand]["aspects"]
    for asp, score in aspects.items():
        if score is not None and score < -0.3 and overall > 0:
            aspect_anomalies.append((brand, asp, score, overall))

aspect_anomalies.sort(key=lambda x: x[2])  # worst aspect first

if aspect_anomalies:
    b, asp, asp_score, overall = aspect_anomalies[0]
    insights.append({
        "id":          3,
        "title":       f"{b}'s {asp.title()} Problem Is Hidden Behind Good Overall Scores",
        "insight":     (
            f"{b} has an overall sentiment polarity of {overall} — positive territory. "
            f"But drilling into aspect-level sentiment reveals a {asp} score of {asp_score}, "
            f"deeply negative. Customers are satisfied overall but consistently "
            f"frustrated with the {asp}. This would never surface from star ratings or "
            f"overall sentiment alone."
        ),
        "implication": (
            f"A product team at a competing brand should highlight {asp} quality in marketing. "
            f"A buyer considering {b} should specifically check {asp}-related reviews before purchasing."
        ),
        "severity": "high",
    })

# ── INSIGHT 4: Premium Price Trap ────────────────────────────────────────────
# Most expensive brand with mediocre sentiment
price_ranked     = sorted(brands, key=lambda b: data[b]["pricing"]["avg_price"] or 0, reverse=True)
most_expensive   = price_ranked[0]
exp_data         = data[most_expensive]
cheapest         = price_ranked[-1]
cheap_data       = data[cheapest]
price_diff       = round(exp_data["pricing"]["avg_price"] - cheap_data["pricing"]["avg_price"], 0)
sentiment_diff   = round(
    exp_data["sentiment"]["avg_weighted_polarity"] -
    cheap_data["sentiment"]["avg_weighted_polarity"], 3
)

insights.append({
    "id":          4,
    "title":       f"{most_expensive} Charges ₹{price_diff} More Than {cheapest} But Sentiment Tells a Different Story",
    "insight":     (
        f"{most_expensive} is the most expensive brand at avg ₹{exp_data['pricing']['avg_price']}, "
        f"while {cheapest} averages ₹{cheap_data['pricing']['avg_price']}. "
        f"That's a ₹{price_diff} premium. "
        f"But sentiment polarity difference is only {sentiment_diff} — "
        f"{'the premium brand actually scores lower' if sentiment_diff < 0 else 'marginally better'}. "
        f"{most_expensive} also has {exp_data['sentiment']['negative_pct']}% negative reviews "
        f"vs {cheap_data['sentiment']['negative_pct']}% for {cheapest}. "
        f"The price premium is not justified by customer experience data."
        if sentiment_diff < 0.1 else
        f"The price premium shows marginal sentiment improvement — questionable value."
    ),
    "implication": (
        f"Buyers paying a premium for {most_expensive} are not getting proportionally better experience. "
        f"{cheapest} delivers comparable or better sentiment at significantly lower cost."
    ),
    "severity": "high" if sentiment_diff < 0 else "medium",
})

# ── INSIGHT 5: MRP Inflation Trap ────────────────────────────────────────────
# Brands with inflated MRP flag — discount is fake
inflated = [
    b for b in brands
    if data[b]["pricing"]["inflated_mrp_flag"]
]
not_inflated = [b for b in brands if b not in inflated]

if inflated and not_inflated:
    avg_discount_inflated     = round(
        sum(data[b]["pricing"]["avg_discount_pct"] for b in inflated) / len(inflated), 1
    )
    avg_discount_not_inflated = round(
        sum(data[b]["pricing"]["avg_discount_pct"] for b in not_inflated) / len(not_inflated), 1
    )
    insights.append({
        "id":          5,
        "title":       f"{', '.join(inflated)} Use Inflated MRP — Their Discounts Are Manufactured",
        "insight":     (
            f"{', '.join(inflated)} show average discounts of {avg_discount_inflated}% — "
            f"flagged as inflated MRP (>70% discount is a known Amazon India dark pattern "
            f"where brands set artificially high list prices to manufacture discount perception). "
            f"In contrast {', '.join(not_inflated)} show {avg_discount_not_inflated}% average discount "
            f"on more realistic MRPs. "
            f"The actual selling prices are similar across brands — "
            f"the discount percentage is meaningless as a value signal here."
        ),
        "implication": (
            f"Buyers should ignore discount % completely for {', '.join(inflated)} "
            f"and compare actual selling prices only. "
            f"Dashboard filters based on discount % will mislead users for these brands."
        ),
        "severity": "medium",
    })

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(insights, f, indent=2, ensure_ascii=False)

print(f"✅ Done! Saved to {OUTPUT}\n")
for ins in insights:
    print(f"[{ins['severity'].upper()}] {ins['title']}")
    print(f"  → {ins['implication']}\n")