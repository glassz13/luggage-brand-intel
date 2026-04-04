# 🧳 Luggage Brand Intel
> Competitive intelligence dashboard for luggage brands on Amazon India — built for Moonshot AI Agent Internship Assignment

**[🚀 Live Dashboard](https://luggage-brand-intel-96woi23brqzhsn5pqslnmv.streamlit.app/)** · **[GitHub](https://github.com/glassz13/luggage-brand-intel)** · Built by **Mohit Kumar Meena**

---

## What this does

Scrapes Amazon India product listings and customer reviews for 5 major luggage brands, runs sentiment and aspect-level analysis, and presents everything in an interactive competitive intelligence dashboard — the kind a product manager or brand strategist would actually use.

Not a static report. A decision-ready tool.

---

## Demo

<!-- INSERT DEMO VIDEO HERE -->

---

## Dashboard Pages

| Page | What it shows |
|------|--------------|
| 🏠 Overview | Sentiment ranking, value-for-money scores, price vs sentiment bubble chart, brand scorecard |
| ⚔️ Brand Comparison | Side-by-side sentiment distribution, pricing, aspect radar chart, top praise & complaints |
| 🔍 Product Drilldown | Filterable product table, price distribution, per-product review explorer |
| 🤖 Agent Insights | 5 non-obvious conclusions auto-generated from review + pricing data, trust signal analysis |
| 💬 Ask the Agent | Groq-powered (LLaMA 3.1) chat agent grounded in real scraped data |

---

## Data Pipeline
```
scraper/scrape.py          →   data/raw/products_final.csv
                               data/raw/reviews_final.csv
                                        ↓
scraper/clean.py           →   data/clean/products_clean.csv
                               data/clean/reviews_clean.csv
                                        ↓
scraper/analyse.py         →   data/brand_summary.json
                               data/insights.json
                               data/reviews_with_aspects.csv
                                        ↓
app.py                     →   Streamlit dashboard
```

---

## Coverage

| Metric | Value |
|--------|-------|
| Brands tracked | 5 (Safari, Skybags, American Tourister, VIP, Aristocrat) |
| Products scraped | 75 |
| Reviews scraped | 312 |
| Aspects analyzed | wheels, zipper, handle, material, durability, size, price |

---

## Key Features

**Sentiment Analysis**
- VADER sentiment scoring per review
- Weighted polarity per brand
- Positive / Neutral / Negative breakdown

**Aspect-Level Analysis**
- 7 aspects tracked per review using keyword extraction
- Radar chart comparison across brands
- Surfaces which brand wins on wheels, zippers, durability etc.

**Pricing Intelligence**
- Average selling price vs MRP per brand
- Discount depth analysis
- Value-for-money score normalised to 0–100
- Combo product detection to avoid skewed averages

**Anomaly Detection**
- High rating + recurring durability complaints
- Review trust signals — unverified purchases, short positive reviews, duplicates

**Agent Insights**
- 5 non-obvious conclusions auto-generated from the full dataset
- Powered by Groq LLaMA 3.1

**Ask the Agent**
- Natural language chat grounded in real scraped data
- Brand-aware context injection
- Conversational, not robotic

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Scraping | Python, Playwright (async), Microsoft Edge persistent context |
| Data cleaning | Pandas, Regex |
| Sentiment | VADER, TextBlob |
| Dashboard | Streamlit, Plotly |
| Chat agent | Groq API (LLaMA 3.1 8B Instant) |
| Storage | CSV, JSON |

---

## Setup
```bash
# 1. Clone
git clone https://github.com/glassz13/luggage-brand-intel
cd luggage-brand-intel

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browser
playwright install chromium

# 4. Scrape data (requires Amazon India login in Edge)
python scraper/scrape.py

# 5. Clean data
python scraper/clean.py

# 6. Run analysis
python scraper/analyse.py

# 7. Launch dashboard
streamlit run app.py
```

### Secrets (for chat agent)
Create `.streamlit/secrets.toml`:
```toml
GROK_API_KEY = "your_groq_api_key_here"
```

---

## Project Structure
```
luggage-brand-intel/
├── app.py                    # Streamlit dashboard
├── requirements.txt
├── scraper/
│   ├── scrape.py             # Amazon scraper (Playwright)
│   ├── clean.py              # Data cleaning + normalization
│   └── analyse.py            # Sentiment + aspect analysis
├── data/
│   ├── raw/                  # Raw scraped data
│   │   ├── products_final.csv
│   │   └── reviews_final.csv
│   └── clean/                # Cleaned + enriched data
│       ├── products_clean.csv
│       ├── reviews_clean.csv
│       ├── reviews_with_aspects.csv
│       ├── brand_summary.json
│       └── insights.json
└── README.md
```

---

## Anti-Detection Approach

Amazon actively blocks scrapers. The scraper handles this through:
- Microsoft Edge persistent context with real user profile and cookies
- Randomised human-like delays between requests
- `webdriver` property masked via init script
- CAPTCHA detection with exponential backoff retry
- Global review hash deduplication to avoid redundant requests
- `sortBy=recent` + star filter rotation to get unique reviews

---

## Data Quality Notes

- **Variant deduplication** — different ASINs for same product (color/size variants) are kept as separate products since they have distinct prices, but their shared reviews are deduplicated via MD5 hash
- **Combo detection** — "Set of 2" listings flagged with `is_combo=True` and excluded from per-unit price analysis
- **Size normalization** — raw cm values bucketed into Cabin / Medium / Large / XL categories
- **Review trust signals** — unverified purchases, suspiciously short positive reviews, and duplicate patterns flagged per brand

---

## Author

**Mohit Kumar Meena**
Built for Moonshot AI Agent Internship Assignment
