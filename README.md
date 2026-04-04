# 🧳 Luggage Brand Intel
### Competitive Intelligence Dashboard — Amazon India Luggage Market

**Built by Mohit Kumar Meena · Moonshot AI Agent Internship Assignment**

**[🚀 Live Dashboard](https://luggage-brand-intel-96woi23brqzhsn5pqslnmv.streamlit.app/)** · **[GitHub](https://github.com/glassz13/luggage-brand-intel)**

---

## Overview

The Indian luggage market on Amazon is crowded, discount-heavy, and review-manipulated. This project turns raw marketplace signals — product listings, pricing, and customer reviews — into a decision-ready competitive intelligence dashboard for 5 major brands: **Safari, Skybags, American Tourister, VIP, and Aristocrat.**

The goal was not to build a report. The goal was to build something a brand manager could actually open, explore, and act on.

---

## Demo

<!-- INSERT DEMO VIDEO HERE -->

---

## Approach

The project follows a four-stage pipeline:
```
Scrape → Clean → Analyse → Present
```

**Scrape**
Amazon India does not have a public API for product or review data. The scraper uses Playwright with a persistent Microsoft Edge profile (real cookies, real login) to navigate search results and review pages. Human-like delays, webdriver masking, and CAPTCHA backoff retry logic are used to avoid detection. Reviews are deduplicated globally using MD5 hashing — so if two product variants share the same review pool (which Amazon does silently), each review is only stored once.

**Clean**
Raw data is normalised — prices cast to float, size strings bucketed into Cabin / Medium / Large / XL categories, combo listings (Set of 2 etc.) flagged separately to avoid skewing per-unit price analysis, and a `product_line` field extracted from titles to group variants.

**Analyse**
VADER sentiment scoring runs on every review. Each review is also scored on 7 aspects — wheels, zipper, handle, material, durability, size, price — using keyword extraction with sentiment context. Brand-level summaries aggregate sentiment, pricing, aspect scores, value-for-money (sentiment adjusted by price band), anomalies, and trust signals. Five non-obvious insights are auto-generated using Groq LLaMA 3.1 over the full dataset context.

**Present**
A Streamlit dashboard with five pages — Overview, Brand Comparison, Product Drilldown, Agent Insights, and a Groq-powered chat agent that answers natural language questions grounded in the scraped data.

---

## Dashboard

| Page | What it answers |
|------|----------------|
| 🏠 Overview | Which brand leads on sentiment? Who offers best value? How does price correlate with satisfaction? |
| ⚔️ Brand Comparison | Head-to-head sentiment, pricing, aspect radar, top praise and complaints per brand |
| 🔍 Product Drilldown | Filter by brand, size, price, rating — explore individual products and their reviews |
| 🤖 Agent Insights | 5 non-obvious conclusions auto-generated from the full dataset with trust signal analysis |
| 💬 Ask the Agent | Natural language chat grounded in real data — "Which brand has the best zipper quality?" |

---

## Data Coverage

| Metric | Value |
|--------|-------|
| Brands | 5 — Safari, Skybags, American Tourister, VIP, Aristocrat |
| Products scraped | 75 (15 per brand) |
| Reviews scraped | 312 |
| Aspects analysed | wheels, zipper, handle, material, durability, size, price |
| Size categories | Cabin ≤56cm · Medium 57–69cm · Large 70–76cm · XL 77cm+ |

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Scraping | Playwright + Edge persistent context | Real browser with actual cookies — far harder to detect than headless requests |
| Sentiment | VADER | Designed for short opinionated text, no training needed, fast |
| Dashboard | Streamlit + Plotly | Fastest path to an interactive shareable UI |
| Chat agent | Groq LLaMA 3.1 8B | Free, fast inference, good enough for grounded Q&A |
| Storage | CSV + JSON | Lightweight, portable, no database overhead needed at this scale |

---

## Limitations

- **10 reviews per product** — Amazon serves the same top 10 reviews regardless of page number for popular products. Pagination returns duplicates. Star filter rotation partially works around this but 312 total reviews is a small sample for a market this size.
- **Variant review sharing** — Amazon pools reviews across color and size variants of the same product silently. The global hash dedup handles this correctly but it means some products contribute zero unique reviews.
- **Sentiment model** — VADER is lexicon-based and misses sarcasm, mixed-language reviews (Hinglish is common on Amazon India), and context-dependent complaints. A fine-tuned transformer would perform significantly better.
- **Static dataset** — data was scraped once. Prices and reviews change daily. The dashboard reflects a snapshot, not live market state.
- **Brand keyword filtering** — brand matching uses keyword lists which can miss sponsored or mislabelled listings and occasionally include false positives.

---

## Future Improvements

- **Scheduled scraping** — run the pipeline weekly and track sentiment and pricing trends over time, turning this from a snapshot into a longitudinal tracker
- **Hinglish sentiment model** — fine-tune a multilingual BERT on Amazon India reviews to handle code-switched text properly
- **Expanded brand coverage** — add Nasher Miles, Uppercase, Level8 to capture the premium and DTC segments
- **Price history tracking** — store price snapshots per ASIN and surface discount patterns (e.g. brands that inflate MRP to fake high discounts)
- **Review authenticity scoring** — build a classifier to detect incentivised or fake reviews beyond the basic trust signals currently implemented
- **Automated insights refresh** — re-run Groq insight generation on each new data pull so the Agent Insights page stays current

---

## Project Structure
```
luggage-brand-intel/
├── app.py                    # Streamlit dashboard (5 pages)
├── requirements.txt
├── scraper/
│   ├── scrape.py             # Playwright scraper — products + reviews
│   ├── clean.py              # Normalisation, size bucketing, dedup
│   └── analyse.py            # Sentiment, aspects, summaries, insights
└── data/
    ├── raw/
    │   ├── products_final.csv
    │   └── reviews_final.csv
    └── clean/
        ├── products_clean.csv
        ├── reviews_clean.csv
        ├── reviews_with_aspects.csv
        ├── brand_summary.json
        └── insights.json
```

---

**Mohit Kumar Meena · Moonshot AI Agent Internship Assignment**
