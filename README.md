# 🧳 Luggage Brands — Amazon India Competitive Intelligence

> Scrape → Analyze → Compare → Decide. Built for the Moonshot AI Agent Internship.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://luggage-brand-intel-96woi23brqzhsn5pqslnmv.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)

---

## What It Does

Pulls Amazon India luggage brand data, runs a full NLP pipeline on customer reviews, and serves a competitive intelligence dashboard answering:

- Which brands win on sentiment vs price?
- Where do star ratings lie but review text tells the truth?
- Which aspects (zipper, wheels, handle...) are failing silently?
- Which brand gives the best value per rupee?

🎥 [Watch walkthrough](https://www.loom.com/share/515072f1acb14a268e929d45b20aa8ba)

**[→ Try the live dashboard](https://luggage-brand-intel-96woi23brqzhsn5pqslnmv.streamlit.app)**

---

## Pipeline
```
scraper.py
    ↓  products + reviews CSVs
sentiment.py
    ↓  BERT sentiment per review (nlptown multilingual)
    ↓  Confidence-weighted polarity (-1 to +1)
    ↓  Aspect extraction — 7 aspects (wheels, zipper, handle,
    ↓  material, durability, size, price)
    ↓  Keyword match → sentence split → BERT on matched sentences
    ↓  TF-IDF themes — top praise + complaints per brand
    ↓  Anomaly detection — hidden dissatisfaction, aspect failures, rating skew
    ↓  Value for money — sentiment adjusted by price band
    ↓  brand_summary.json
insights.py
    ↓  5 non-obvious insights generated from structured data
    ↓  insights.json
app.py  →  Streamlit dashboard + Groq AI agent
```

---

## Dashboard Views

| View | What it shows |
|------|--------------|
| 🏠 Overview | Sentiment ranking, VFM scores, pricing bubble chart, brand scorecard |
| ⚔️ Brand Comparison | Radar chart across 7 aspects, sentiment distribution, themes side by side |
| 🔍 Product Drilldown | Filterable product table with per-review BERT predictions |
| 🤖 Agent Insights | 5 auto-generated non-obvious conclusions from the data |
| 💬 Ask the Agent | Groq-powered AI answers brand questions from structured data |

---

## Tech Stack

| | Tool | Why |
|-|------|-----|
| Scraping | Playwright | Handles dynamic Amazon pages |
| Sentiment | `nlptown/bert-base-multilingual-uncased-sentiment` | Trained on product reviews, handles Hinglish, far better than SST-2 for Amazon India |
| Aspects | Keyword match + BERT on sentences | Fixed taxonomy = faster, more controllable than full ABSA models |
| Themes | TF-IDF | Fast, interpretable, scales to 30k reviews without GPU |
| Dashboard | Streamlit + Plotly | Rapid deployment, production-grade charts |
| AI Agent | Groq API (LLaMA 3.1) | Fast inference, context-sliced per query to keep tokens low |

---

## Key Findings (Auto-generated)

1. **Safari has the biggest star rating vs sentiment gap** — 4.07★ but BERT polarity -0.154. Stars are unreliable here.
2. **Skybags is the value winner** — highest sentiment (0.227) at lowest avg price (₹2,178). VFM: 100/100.
3. **VIP's handle is a hidden failure** — positive overall (0.024) but handle aspect scores -0.402.
4. **VIP charges ₹1,732 more than Skybags with worse sentiment** — premium not justified.
5. **Safari and Aristocrat inflate MRP** — 78-79% "discounts" are manufactured perception.

---

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

To re-run the full pipeline after scraping new data:
```bash
python scraper.py
python sentiment.py
python insights.py
streamlit run app.py
```

---

## File Structure
```
luggage-brand-intel/
├── app.py              # Streamlit dashboard
├── scraper.py          # Amazon India scraper
├── sentiment.py        # Full NLP pipeline → brand_summary.json
├── insights.py         # Auto-generates insights.json
├── requirements.txt
└── data/
    ├── clean/
    │   ├── products_clean.csv
    │   └── reviews_clean.csv
    └── analyzed/
        ├── brand_summary.json
        ├── reviews_with_aspects.csv
        └── insights.json
```

---

## Limitations & How to Scale

**Current state:** 312 reviews, 5 brands — proof of concept. Directionally correct but statistically thin. 2,000+ reviews per brand makes conclusions significantly more reliable.

**To scale to 50k reviews + more brands:**

- Switch `device=-1` to `device=0` in `sentiment.py` for GPU — 15x faster BERT inference
- Replace the AI agent's JSON slice injection with **RAG** — chunk reviews by brand+aspect, embed with `sentence-transformers`, store in ChromaDB, retrieve top-k chunks per query. Enables answering *"show me exact reviews where VIP handle broke"*
- Scraper already brand-agnostic — add Nasher Miles, Samsonite etc by updating the brand list only
- Move to FastAPI + React for production, keep `sentiment.py` as a nightly batch job

---

## Author

**Mohit Kumar** · [LinkedIn](https://www.linkedin.com/in/mohit-kumar-116753375/)

Built for the Moonshot AI Agent Internship Assignment · April 2026
