# 🧳 Luggage Brand Intel

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Playwright](https://img.shields.io/badge/Scraping-Playwright-green?style=flat-square)
![BERT](https://img.shields.io/badge/Sentiment-BERT%20Multilingual-purple?style=flat-square)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-ff4b4b?style=flat-square&logo=streamlit)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.1-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

Competitive intelligence dashboard for luggage brands on Amazon India. Scrapes product listings and customer reviews, runs BERT sentiment and aspect-level analysis with TF-IDF theme extraction, and surfaces decision-ready insights through an interactive Streamlit dashboard with a Groq-powered chat agent.

> Built by **Mohit Kumar Meena** · Moonshot AI Agent Internship Assignment

**[🚀 Live Dashboard](https://luggage-brand-intel-96woi23brqzhsn5pqslnmv.streamlit.app/)** · **[GitHub](https://github.com/glassz13/luggage-brand-intel)**

---

## Demo

<!-- INSERT DEMO VIDEO HERE -->

---

## 📊 Coverage

| Metric | Value |
|--------|-------|
| Brands tracked | 5 — Safari, Skybags, American Tourister, VIP, Aristocrat |
| Products scraped | 75 (15 per brand) |
| Reviews scraped | 312 |
| Aspects analysed | wheels, zipper, handle, material, durability, size, price |
| Size categories | Cabin ≤56cm · Medium 57–69cm · Large 70–76cm · XL 77cm+ |

---

## 🗂️ Project Structure
```
luggage-brand-intel/
├── app.py                         # Streamlit dashboard — 5 pages
├── scraper.py                     # Playwright scraper — products + reviews
├── sentiment.py                   # BERT sentiment + aspect extraction + brand_summary.json
├── insights.py                    # 5 non-obvious insights — pure logic, no API
├── requirements.txt
├── .streamlit/
│   └── secrets.toml               # Groq API key
└── data/
    ├── products_clean.csv
    ├── reviews_clean.csv
    ├── reviews_with_aspects.csv
    ├── brand_summary.json
    └── insights.json
```

---

## 🔧 What's Inside

### `scraper.py` — Data Collection
- Playwright with persistent Microsoft Edge profile — real cookies, real login, much harder to fingerprint than headless requests
- `webdriver` property masked via init script with randomised human-like delays between every request
- CAPTCHA detection with exponential backoff retry — waits and retries instead of immediately failing
- Global MD5 review hash deduplication across all products — Amazon silently pools reviews across color and size variants of the same product, this ensures each unique review is stored exactly once
- `sortBy=recent` on review pages to avoid Amazon recycling the same top-10 reviews repeatedly
- Product meta (title, review count, size) filled in a single page visit during review scraping — no redundant requests

### `sentiment.py` — Analysis Pipeline

**Step 1 — BERT Sentiment per Review**
- Model: `nlptown/bert-base-multilingual-uncased-sentiment` — 5-class star predictor, multilingual, handles mixed English-Hindi text better than English-only models
- Confidence-weighted polarity: `polarity × confidence_score` so a high-confidence negative review counts more than an uncertain one
- Outputs `star_prediction`, `sentiment_polarity`, and `weighted_polarity` per review

**Step 2 — Aspect Extraction**
- 7 aspects tracked: wheels, zipper, handle, material, durability, size, price
- Sentence-level extraction — each review is split into sentences, matched against aspect keyword lists
- BERT runs on matched sentences separately — aspect score is confidence-weighted average polarity of all sentences mentioning that aspect
- Aspect coverage reported per brand — shows which aspects have enough data to trust

**Step 3 — TF-IDF Theme Extraction**
- `TfidfVectorizer` with 1–3 ngrams on positive (≥4 star) and negative (≤2 star) review subsets per brand
- Custom stopword list strips generic luggage words (bag, trolley, product, quality) to surface meaningful phrases
- Outputs `top_praise` and `top_complaints` with real review sentence examples per brand

**Step 4 — Anomaly Detection**
Three anomaly types detected per brand:
1. **Hidden dissatisfaction** — reviews that gave 4–5 stars but BERT reads as negative text. Common on Amazon India where buyers rate generously under social pressure
2. **Aspect anomaly** — overall sentiment positive but a specific aspect (e.g. zipper) scores deeply negative. Would never surface from star ratings alone
3. **Rating skew** — >60% five-star with <5% one-star, flagged as potentially inflated

**Step 5 — Review Trust Signals**
- Unverified purchase percentage per brand
- Suspiciously short high-confidence positive reviews (< 5 words, 5-star prediction, confidence > 0.85)
- Near-duplicate detection via first-50-char prefix hashing

**Step 6 — Value for Money**
- VFM raw score: `avg_weighted_sentiment / (avg_price / 1000)` — higher sentiment at lower price = better value
- Normalised to 0–100 across all brands for dashboard display
- Sentiment broken down by price band (budget / mid / premium) per brand

**Step 7 — MRP Inflation Detection**
- Brands with average discount > 70% flagged as `inflated_mrp_flag = True`
- Known dark pattern on Amazon India — artificially high list prices manufacture discount perception while actual selling prices stay similar across brands

### `insights.py` — 5 Non-Obvious Conclusions
Pure deterministic logic over `brand_summary.json` — no API calls, reproducible every run:

1. **Star vs BERT disconnect** — brand with biggest gap between average star rating and BERT-derived polarity score. Surfaces where surface metrics lie
2. **Hidden gem** — brand with highest VFM score that isn't the most reviewed. Budget buyers relying on review count alone will miss it
3. **Aspect anomaly** — brand with good overall sentiment but one aspect scoring deeply negative. The failure hidden behind aggregate scores
4. **Premium price trap** — most expensive brand vs cheapest, sentiment difference vs price difference. Whether the premium is justified by customer experience data
5. **MRP inflation** — brands with inflated MRP flagged, average discount compared against non-inflated brands. Discount % shown to be meaningless as a value signal

### `app.py` — Dashboard

| Page | What it answers |
|------|----------------|
| 🏠 Overview | Which brand leads sentiment? Who offers best value? Price vs sentiment bubble chart, full brand scorecard |
| ⚔️ Brand Comparison | Head-to-head sentiment distribution, pricing depth, 7-aspect radar chart, top praise and complaints |
| 🔍 Product Drilldown | Filter by brand, size, price range, rating — explore products and per-product review sentiment |
| 🤖 Agent Insights | 5 auto-generated non-obvious conclusions, anomaly cards, review trust signal table |
| 💬 Ask the Agent | Groq LLaMA 3.1 chat grounded in real scraped data — brand-aware context injection, conversational tone |

---

## 🛠️ Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Scraping | Playwright + Edge persistent context | Real browser session with actual cookies — far harder to fingerprint than bare requests |
| Sentiment | `nlptown/bert-base-multilingual-uncased-sentiment` | Multilingual, handles Hinglish better than English-only models, 5-class output maps directly to polarity |
| Theme extraction | TF-IDF (sklearn) with custom stopwords | Fast, interpretable, no hallucination — extracts what customers actually wrote |
| Aspect analysis | Keyword matching + sentence-level BERT | Targeted sentiment on relevant sentences only — more signal, less noise than full-review aspect scoring |
| Dashboard | Streamlit + Plotly | Fastest path to an interactive, filterable, shareable UI |
| Chat agent | Groq LLaMA 3.1 8B Instant | Free, extremely fast inference, sufficient for grounded Q&A over structured JSON context |
| Storage | CSV + JSON | Lightweight and portable — no database overhead needed at this scale |

---

## ⚠️ Limitations

- **~10 reviews per product** — Amazon serves the same top-10 reviews regardless of page number for popular products. Pagination returns exact duplicates. 312 total reviews is a small sample for a market this size — limits statistical reliability of aspect scores for less-mentioned aspects like handle and zipper
- **Variant review sharing** — Amazon pools reviews across color and size variants silently. Global hash dedup handles this correctly but some product ASINs contribute zero unique reviews as a result
- **Hinglish coverage** — while BERT multilingual handles mixed text better than VADER, it was not trained specifically on Indian e-commerce reviews. Code-switched sentences and transliterated Hindi still introduce noise
- **Static snapshot** — data scraped once. Prices and rankings change daily. The dashboard reflects a point-in-time view, not live market state
- **Small brand keyword lists** — brand matching uses curated keyword lists which can miss sponsored or mislabelled listings and occasionally include false positives for short keywords like "VIP"

---

## 🔮 Future Improvements

- **Scheduled pipeline** — run scrape → analyse weekly and track sentiment and price trends over time, turning this from a snapshot into a longitudinal market tracker
- **Price history per ASIN** — store price snapshots over time to detect brands that seasonally inflate MRP before sales events to manufacture larger discounts
- **Fine-tuned sentiment model** — train on Amazon India luggage reviews specifically, or use a Hinglish-aware model to handle code-switched text properly
- **Expanded brand coverage** — add Nasher Miles, Uppercase, and Level8 to capture the premium and DTC segments missing from this analysis
- **Review authenticity classifier** — train a supervised model on known fake/genuine review patterns to go beyond the heuristic trust signals currently implemented
- **Automated insight refresh** — re-run `insights.py` on each new data pull so the Agent Insights page stays current without manual intervention

---

## 👤 Author

**Mohit Kumar Meena**  
IIT Delhi — Engineering Physics  
[GitHub](https://github.com/glassz13)
