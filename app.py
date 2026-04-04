"""
app.py
Luggage Intel — Competitive Intelligence Dashboard
Run: streamlit run app.py
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from openai import OpenAI

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Luggage Brand Intel",
    page_icon  = "🧳",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Theme / CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    .stApp {
        background-color: #0a0a0f;
        color: #f1f5f9;
    }

    [data-testid="stSidebar"] {
        background-color: #0f0f1a;
        border-right: 1px solid #1e1e2e;
    }

    /* All default streamlit text → white */
    p, span, div, label {
        color: #f1f5f9;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d2d44;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #818cf8;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 4px;
    }

    /* Insight cards */
    .insight-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d2d44;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        border-left: 4px solid #6366f1;
    }
    .insight-card.high   { border-left-color: #ef4444; }
    .insight-card.medium { border-left-color: #f59e0b; }
    .insight-card.low    { border-left-color: #22c55e; }

    .insight-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 10px;
    }
    .insight-text {
        font-size: 0.875rem;
        color: #e2e8f0;
        line-height: 1.6;
        margin-bottom: 12px;
    }
    .insight-implication {
        font-size: 0.85rem;
        color: #c7d2fe;
        background: rgba(99, 102, 241, 0.12);
        border-radius: 8px;
        padding: 10px 14px;
    }

    /* Severity badge */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .badge-high   { background: rgba(239,68,68,0.2);  color: #fca5a5; }
    .badge-medium { background: rgba(245,158,11,0.2); color: #fcd34d; }
    .badge-low    { background: rgba(34,197,94,0.2);  color: #86efac; }

    /* Chat */
    .chat-message {
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 10px;
        font-size: 0.875rem;
        line-height: 1.6;
    }
    .chat-user {
        background: rgba(99,102,241,0.15);
        border: 1px solid rgba(99,102,241,0.3);
        margin-left: 20%;
        color: #e0e7ff;
    }
    .chat-agent {
        background: #1a1a2e;
        border: 1px solid #2d2d44;
        margin-right: 20%;
        color: #f1f5f9;
    }
    .chat-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 6px;
        color: #94a3b8;
    }

    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 4px;
    }
    .section-sub {
        font-size: 0.875rem;
        color: #cbd5e1;
        margin-bottom: 24px;
    }

    /* Brand pill */
    .brand-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(99,102,241,0.15);
        color: #c7d2fe;
        border: 1px solid rgba(99,102,241,0.3);
        margin-right: 6px;
    }

    /* Anomaly card */
    .anomaly-card {
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .anomaly-brand {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .anomaly-desc {
        font-size: 0.875rem;
        color: #e2e8f0;
        margin-top: 6px;
    }

    /* Theme items */
    .theme-item {
        font-size: 0.82rem;
        color: #e2e8f0;
        padding: 2px 0;
    }

    /* Sidebar labels */
    .sidebar-label {
        font-size: 0.7rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 10px;
    }

    /* Sidebar stats */
    .sidebar-stats {
        font-size: 0.8rem;
        color: #cbd5e1;
    }

    /* Streamlit widget labels */
    .stMultiSelect label,
    .stSlider label,
    .stSelectbox label,
    .stRadio label {
        color: #f1f5f9 !important;
        font-size: 0.875rem !important;
    }

    /* Streamlit multiselect tags */
    .stMultiSelect span {
        color: #f1f5f9 !important;
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Hide streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0a0a0f; }
    ::-webkit-scrollbar-thumb { background: #2d2d44; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Brand colors ──────────────────────────────────────────────────────────────
BRAND_COLORS = {
    "Skybags":            "#6366f1",
    "Aristocrat":         "#22c55e",
    "American Tourister": "#f59e0b",
    "VIP":                "#ec4899",
    "Safari":             "#ef4444",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(family="Space Grotesk", color="#e2e8f0", size=12),
    margin        = dict(l=20, r=20, t=40, b=20),
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("data/brand_summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    with open("data/insights.json", encoding="utf-8") as f:
        insights = json.load(f)
    products = pd.read_csv("data/products_clean.csv")
    reviews  = pd.read_csv("data/reviews_with_aspects.csv")
    return summary, insights, products, reviews

summary, insights, products, reviews = load_data()
brands = list(summary.keys())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 20px 0 30px;'>
        <div style='font-size:1.6rem;font-weight:700;color:#f1f5f9;'>🧳 Brand Intel</div>
        <div style='font-size:0.8rem;color:#cbd5e1;margin-top:4px;'>Amazon India · Competitive Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠  Overview", "⚔️  Brand Comparison", "🔍  Product Drilldown", "🤖  Agent Insights", "💬  Ask the Agent"],
        label_visibility = "collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-label'>Tracking Brands</div>", unsafe_allow_html=True)
    pills = "".join([f"<span class='brand-pill'>{b}</span>" for b in brands])
    st.markdown(f"<div style='line-height:2.4;'>{pills}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    total_reviews  = sum(summary[b]["sentiment"]["total_reviews"] for b in brands)
    total_products = sum(summary[b]["ratings"]["total_products"]  for b in brands)
    st.markdown(f"<div class='sidebar-stats'>📦 {total_products} products &nbsp;|&nbsp; 💬 {total_reviews} reviews</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Overview":
    st.markdown("<div class='section-header'>Market Overview</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Luggage brands on Amazon India · Sentiment, pricing and value snapshot</div>", unsafe_allow_html=True)

    # ── Top metrics ───────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    avg_sentiment = sum(summary[b]["sentiment"]["avg_weighted_polarity"] for b in brands) / len(brands)
    avg_price     = sum(summary[b]["pricing"]["avg_price"] or 0 for b in brands) / len(brands)

    metrics = [
        (c1, str(len(brands)),        "Brands Tracked"),
        (c2, str(total_products),     "Products Analyzed"),
        (c3, str(total_reviews),      "Reviews Analyzed"),
        (c4, f"{avg_sentiment:+.2f}", "Avg Sentiment"),
        (c5, f"₹{int(avg_price)}",    "Avg Price"),
    ]
    for col, val, label in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{val}</div>
                <div class='metric-label'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Sentiment ranking + VFM ───────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Sentiment Ranking</div>", unsafe_allow_html=True)
        sent_data = sorted(
            [(b, summary[b]["sentiment"]["avg_weighted_polarity"]) for b in brands],
            key=lambda x: x[1]
        )
        fig = go.Figure(go.Bar(
            x           = [s[1] for s in sent_data],
            y           = [s[0] for s in sent_data],
            orientation = "h",
            marker      = dict(color=[BRAND_COLORS.get(s[0], "#6366f1") for s in sent_data], opacity=0.9),
            text        = [f"{s[1]:+.3f}" for s in sent_data],
            textfont    = dict(family="JetBrains Mono", size=12, color="#f1f5f9"),
            hovertemplate = "<b>%{y}</b><br>Polarity: %{x:.3f}<extra></extra>",
        ))
        fig.add_vline(x=0, line_color="#3d3d5c", line_width=1.5)
        fig.update_layout(
            **PLOTLY_LAYOUT, height=300,
            xaxis=dict(gridcolor="#1e1e2e", zeroline=False, title="Weighted Sentiment Polarity", tickfont=dict(color="#e2e8f0")),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#f1f5f9")),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Value for Money</div>", unsafe_allow_html=True)
        vfm_data = sorted(
            [(b, summary[b]["value_for_money"].get("vfm_score_normalized", 0)) for b in brands],
            key=lambda x: x[1], reverse=True
        )
        fig2 = go.Figure(go.Bar(
            x             = [v[0] for v in vfm_data],
            y             = [v[1] for v in vfm_data],
            marker        = dict(color=[BRAND_COLORS.get(v[0], "#6366f1") for v in vfm_data], opacity=0.9),
            text          = [f"{v[1]:.0f}" for v in vfm_data],
            textfont      = dict(family="JetBrains Mono", size=12, color="#f1f5f9"),
            hovertemplate = "<b>%{x}</b><br>VFM Score: %{y:.1f}/100<extra></extra>",
        ))
        fig2.update_layout(
            **PLOTLY_LAYOUT, height=300,
            yaxis=dict(gridcolor="#1e1e2e", range=[0,115], title="VFM Score (0–100)", tickfont=dict(color="#e2e8f0")),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#f1f5f9")),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Bubble chart ──────────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Price vs Sentiment vs Review Volume</div>", unsafe_allow_html=True)
    bubble_data = [{
        "Brand":     b,
        "Avg Price": summary[b]["pricing"]["avg_price"] or 0,
        "Sentiment": summary[b]["sentiment"]["avg_weighted_polarity"],
        "Reviews":   summary[b]["sentiment"]["total_reviews"],
        "VFM":       summary[b]["value_for_money"].get("vfm_score_normalized", 0),
    } for b in brands]
    bdf = pd.DataFrame(bubble_data)

    fig3 = px.scatter(
        bdf, x="Avg Price", y="Sentiment",
        size="Reviews", color="Brand",
        color_discrete_map = BRAND_COLORS,
        hover_name="Brand",
        hover_data={"VFM": True, "Reviews": True},
        size_max=60,
    )
    fig3.update_layout(
        **PLOTLY_LAYOUT, height=380,
        xaxis=dict(gridcolor="#1e1e2e", title="Average Selling Price (₹)", tickfont=dict(color="#e2e8f0")),
        yaxis=dict(gridcolor="#1e1e2e", title="Weighted Sentiment Polarity", zeroline=True, zerolinecolor="#2d2d44", tickfont=dict(color="#e2e8f0")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#f1f5f9")),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Scorecard table ───────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Brand Scorecard</div>", unsafe_allow_html=True)
    rows = []
    for b in brands:
        d = summary[b]
        rows.append({
            "Brand":       b,
            "Sentiment":   d["sentiment"]["avg_weighted_polarity"],
            "Positive %":  d["sentiment"]["positive_pct"],
            "Negative %":  d["sentiment"]["negative_pct"],
            "Avg Price ₹": d["pricing"]["avg_price"],
            "Avg Rating":  d["ratings"]["avg_star_rating"],
            "VFM Score":   d["value_for_money"].get("vfm_score_normalized"),
            "Reviews":     d["sentiment"]["total_reviews"],
            "Anomalies":   len(d["anomalies"]),
        })
    scorecard = pd.DataFrame(rows).set_index("Brand")
    st.dataframe(
        scorecard.style
            .background_gradient(subset=["Sentiment"],  cmap="RdYlGn", vmin=-0.5, vmax=0.5)
            .background_gradient(subset=["VFM Score"],  cmap="YlGn")
            .background_gradient(subset=["Negative %"], cmap="Reds")
            .format({
                "Sentiment":   "{:+.3f}",
                "Positive %":  "{:.1f}%",
                "Negative %":  "{:.1f}%",
                "Avg Price ₹": "₹{:.0f}",
                "Avg Rating":  "{:.2f}",
                "VFM Score":   "{:.1f}",
            }),
        use_container_width=True,
        height=250,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — BRAND COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚔️  Brand Comparison":
    st.markdown("<div class='section-header'>Brand Comparison</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Compare brands head to head across sentiment, pricing, and aspect quality</div>", unsafe_allow_html=True)

    selected = st.multiselect(
        "Select brands to compare",
        options = brands,
        default = brands,
    )

    if len(selected) < 2:
        st.warning("Select at least 2 brands to compare.")
        st.stop()

    # ── Sentiment distribution ────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Sentiment Distribution</div>", unsafe_allow_html=True)
        fig = go.Figure()
        for b in selected:
            d = summary[b]["sentiment"]
            fig.add_trace(go.Bar(
                name         = b,
                x            = ["Positive", "Neutral", "Negative"],
                y            = [d["positive_pct"], d["neutral_pct"], d["negative_pct"]],
                marker_color = BRAND_COLORS.get(b, "#6366f1"),
                opacity      = 0.85,
            ))
        fig.update_layout(
            **PLOTLY_LAYOUT, height=320, barmode="group",
            yaxis=dict(gridcolor="#1e1e2e", title="%", tickfont=dict(color="#e2e8f0")),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#f1f5f9")),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#f1f5f9")),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Pricing Comparison</div>", unsafe_allow_html=True)
        fig2 = go.Figure()
        for b in selected:
            p = summary[b]["pricing"]
            fig2.add_trace(go.Bar(
                name         = b,
                x            = [b],
                y            = [p["avg_price"] or 0],
                marker_color = BRAND_COLORS.get(b, "#6366f1"),
                opacity      = 0.85,
                text         = [f"₹{p['avg_price']:.0f}"],
                textposition = "outside",
                textfont     = dict(color="#f1f5f9"),
                hovertemplate = (
                    f"<b>{b}</b><br>Avg Price: ₹{p['avg_price']:.0f}<br>"
                    f"Avg MRP: ₹{p['avg_mrp']:.0f}<br>"
                    f"Discount: {p['avg_discount_pct']:.1f}%<extra></extra>"
                ),
            ))
        fig2.update_layout(
            **PLOTLY_LAYOUT, height=320, showlegend=False,
            yaxis=dict(gridcolor="#1e1e2e", title="Avg Selling Price (₹)", tickfont=dict(color="#e2e8f0")),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#f1f5f9")),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Aspect radar ──────────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Aspect Sentiment Radar</div>", unsafe_allow_html=True)
    aspects = ["wheels", "zipper", "handle", "material", "durability", "size", "price"]

    fig3 = go.Figure()
    for b in selected:
        asp    = summary[b]["aspects"]
        values = [asp.get(a) or 0 for a in aspects]
        values_closed = values + [values[0]]

        fig3.add_trace(go.Scatterpolar(
            r          = values_closed,
            theta      = aspects + [aspects[0]],
            fill       = "toself",
            name       = b,
            line_color = BRAND_COLORS.get(b, "#6366f1"),
            fillcolor  = BRAND_COLORS.get(b, "#6366f1"),
            opacity    = 0.2,
        ))
        fig3.add_trace(go.Scatterpolar(
            r          = values_closed,
            theta      = aspects + [aspects[0]],
            mode       = "lines+markers",
            name       = b,
            line_color = BRAND_COLORS.get(b, "#6366f1"),
            showlegend = False,
            opacity    = 0.9,
        ))

    fig3.update_layout(
        **PLOTLY_LAYOUT, height=500,
        polar=dict(
            bgcolor     = "rgba(0,0,0,0)",
            radialaxis  = dict(
                visible   = True,
                range     = [-1, 1],
                gridcolor = "#2d2d44",
                color     = "#e2e8f0",
                tickfont  = dict(color="#e2e8f0"),
            ),
            angularaxis = dict(
                gridcolor = "#2d2d44",
                color     = "#f1f5f9",
                tickfont  = dict(color="#f1f5f9", size=13),
            ),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#f1f5f9")),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Themes comparison ─────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:16px;'>Top Praise & Complaints</div>", unsafe_allow_html=True)
    cols = st.columns(len(selected))
    for i, b in enumerate(selected):
        with cols[i]:
            color = BRAND_COLORS.get(b, "#6366f1")
            st.markdown(f"<div style='color:{color};font-weight:600;font-size:0.95rem;margin-bottom:12px;'>{b}</div>", unsafe_allow_html=True)
            praise     = summary[b]["themes"].get("top_praise",     [])[:5]
            complaints = summary[b]["themes"].get("top_complaints", [])[:5]
            st.markdown("<div style='color:#86efac;font-size:0.82rem;font-weight:600;margin-bottom:4px;'>✅ Praise</div>", unsafe_allow_html=True)
            for p in praise:
                st.markdown(f"<div class='theme-item'>• {p}</div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#fca5a5;font-size:0.82rem;font-weight:600;margin-top:10px;margin-bottom:4px;'>❌ Complaints</div>", unsafe_allow_html=True)
            for c in complaints:
                st.markdown(f"<div class='theme-item'>• {c}</div>", unsafe_allow_html=True)

    # ── Anomalies ─────────────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-top:8px;margin-bottom:12px;'>Detected Anomalies</div>", unsafe_allow_html=True)
    has_anomaly = False
    for b in selected:
        for ano in summary[b]["anomalies"]:
            has_anomaly = True
            sev   = ano.get("severity", "medium")
            color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}.get(sev, "#6366f1")
            st.markdown(f"""
            <div style='background:#1a1a2e;border:1px solid #2d2d44;border-left:4px solid {color};
                        border-radius:8px;padding:14px 18px;margin-bottom:10px;'>
                <div style='color:{color};font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;'>
                    {sev} · {b}
                </div>
                <div style='color:#e2e8f0;font-size:0.875rem;margin-top:6px;'>{ano['description']}</div>
            </div>
            """, unsafe_allow_html=True)
    if not has_anomaly:
        st.info("No anomalies detected for selected brands.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PRODUCT DRILLDOWN
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍  Product Drilldown":
    st.markdown("<div class='section-header'>Product Drilldown</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Explore individual products, pricing, and review sentiment</div>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        sel_brands = st.multiselect("Brand", brands, default=brands)
    with fc2:
        all_sizes  = sorted(products["size_category"].dropna().unique().tolist())
        sel_sizes  = st.multiselect("Size Category", all_sizes, default=all_sizes)
    with fc3:
        price_min, price_max = st.slider(
            "Price Range (₹)",
            min_value = int(products["price"].min()),
            max_value = int(products["price"].max()),
            value     = (int(products["price"].min()), int(products["price"].max())),
        )
    with fc4:
        min_rating = st.slider("Min Rating", 1.0, 5.0, 1.0, 0.1)

    filtered = products[
        (products["brand"].isin(sel_brands)) &
        (products["size_category"].isin(sel_sizes)) &
        (products["price"].between(price_min, price_max)) &
        (products["rating"] >= min_rating)
    ].copy()

    st.markdown(f"<div style='color:#cbd5e1;font-size:0.85rem;margin-bottom:16px;'>{len(filtered)} products match filters</div>", unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No products match the selected filters.")
        st.stop()

    display_cols = [c for c in ["brand","title","size_category","price","mrp","discount_pct","rating","review_count"] if c in filtered.columns]
    st.dataframe(
        filtered[display_cols].style
            .background_gradient(subset=["rating"],       cmap="YlGn",  vmin=1, vmax=5)
            .background_gradient(subset=["discount_pct"], cmap="Blues")
            .format({
                "price":        "₹{:.0f}",
                "mrp":          "₹{:.0f}",
                "discount_pct": "{:.1f}%",
                "rating":       "{:.1f}",
                "review_count": "{:,.0f}",
            }),
        use_container_width=True,
        height=350,
    )

    # ── Price distribution ────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Price Distribution by Brand</div>", unsafe_allow_html=True)
    fig = px.box(
        filtered, x="brand", y="price",
        color              = "brand",
        color_discrete_map = BRAND_COLORS,
        points             = "all",
        hover_data         = ["title", "size_category"],
    )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=380,
        yaxis      = dict(gridcolor="#1e1e2e", title="Price (₹)", tickfont=dict(color="#e2e8f0")),
        xaxis      = dict(gridcolor="rgba(0,0,0,0)", title="", tickfont=dict(color="#f1f5f9")),
        showlegend = False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Review examples ───────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-bottom:12px;'>Review Examples for a Product</div>", unsafe_allow_html=True)
    selected_product = st.selectbox(
        "Select a product",
        options     = filtered["asin"].tolist(),
        format_func = lambda x: (
            filtered[filtered["asin"]==x]["title"].values[0][:80] + "..."
            if len(filtered[filtered["asin"]==x]["title"].values[0]) > 80
            else filtered[filtered["asin"]==x]["title"].values[0]
        ),
    )

    prod_reviews = reviews[reviews["asin"] == selected_product][
        ["star_rating","star_prediction","sentiment_polarity","review_body"]
    ].head(10)

    if not prod_reviews.empty:
        for _, row in prod_reviews.iterrows():
            pol   = row.get("sentiment_polarity", 0) or 0
            color = "#22c55e" if pol > 0 else "#ef4444" if pol < 0 else "#f59e0b"
            st.markdown(f"""
            <div style='background:#1a1a2e;border:1px solid #2d2d44;border-radius:8px;
                        padding:12px 16px;margin-bottom:8px;border-left:3px solid {color};'>
                <div style='font-size:0.75rem;color:#cbd5e1;margin-bottom:6px;'>
                    ⭐ {row.get('star_rating','?')} actual &nbsp;|&nbsp;
                    🤖 {row.get('star_prediction','?')} predicted &nbsp;|&nbsp;
                    <span style='color:{color};font-family:JetBrains Mono;'>polarity {pol:+.1f}</span>
                </div>
                <div style='font-size:0.875rem;color:#e2e8f0;line-height:1.6;'>{str(row.get('review_body',''))[:300]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No reviews found for this product.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — AGENT INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖  Agent Insights":
    st.markdown("<div class='section-header'>Agent Insights</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>5 non-obvious conclusions auto-generated from review and pricing data</div>", unsafe_allow_html=True)

    for ins in insights:
        sev = ins.get("severity", "medium")
        st.markdown(f"""
        <div class='insight-card {sev}'>
            <div><span class='badge badge-{sev}'>{sev} priority</span></div>
            <div class='insight-title'>💡 {ins['title']}</div>
            <div class='insight-text'>{ins['insight']}</div>
            <div class='insight-implication'>→ {ins['implication']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Trust signals ─────────────────────────────────────────────────────────
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#f1f5f9;margin-top:8px;margin-bottom:12px;'>Review Trust Signals</div>", unsafe_allow_html=True)
    trust_rows = []
    for b in brands:
        t = summary[b]["trust_signals"]
        trust_rows.append({
            "Brand":             b,
            "Unverified %":      t.get("unverified_purchase_pct", 0),
            "Short +ve Reviews": t.get("short_positive_count", 0),
            "Duplicates":        t.get("duplicate_review_count", 0),
        })
    trust_df = pd.DataFrame(trust_rows).set_index("Brand")
    st.dataframe(
        trust_df.style
            .background_gradient(subset=["Unverified %"],      cmap="Oranges")
            .background_gradient(subset=["Short +ve Reviews"], cmap="Oranges")
            .format({"Unverified %": "{:.1f}%"}),
        use_container_width=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — ASK THE AGENT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬  Ask the Agent":
    st.markdown("<div class='section-header'>Ask the Agent</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Powered by Groq (LLaMA 3.1) · Ask anything about luggage brands on Amazon India</div>", unsafe_allow_html=True)

    # Example questions
    st.markdown("""
    <div style='background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:16px 20px;margin-bottom:24px;'>
        <div style='font-size:0.75rem;color:#cbd5e1;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;'>
            Example questions
        </div>
        <div style='display:flex;flex-wrap:wrap;gap:8px;'>
    """ + "".join([
        f"<span style='background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);"
        f"border-radius:6px;padding:5px 14px;font-size:0.82rem;color:#c7d2fe;'>{q}</span>"
        for q in [
            "Which brand has the best zipper quality?",
            "Is VIP worth the premium price?",
            "Which brand should I buy under ₹2500?",
            "Why is Safari underperforming?",
            "Which brand wins on durability?",
        ]
    ]) + "</div></div>", unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── Groq client ───────────────────────────────────────────────────────────
    groq_client = OpenAI(
        api_key  = st.secrets["GROK_API_KEY"],
        base_url = "https://api.groq.com/openai/v1",
    )

    BRAND_ALIASES = {
        "american tourister": "American Tourister",
        "safari":             "Safari",
        "skybags":            "Skybags",
        "vip":                "VIP",
        "aristocrat":         "Aristocrat",
    }
    SYSTEM_PROMPT = """You are a friendly competitive intelligence assistant for luggage brands on Amazon India.
You have access to structured data including sentiment scores, pricing, aspect-level sentiment,
themes, anomalies, and value-for-money scores derived from real customer reviews.

Personality:
- Be warm and conversational, like a knowledgeable friend — not a formal report.
- For greetings or small talk (hi, hello, how are you), respond naturally and briefly.
  Example: "Hey! 👋 What would you like to know about luggage brands?"
- For data questions, give a clear recommendation in plain language first,
  then back it up with numbers. Don't lead with metrics.
  Example: "Honestly, Skybags is the best bang for your buck right now —
  highest customer satisfaction (0.227 sentiment) at the lowest avg price (₹2,178)."
- Use "honestly", "actually", "looks like" to sound natural.
- Avoid bullet-point dumps. Prefer 2-3 flowing sentences.

Rules:
- Never hallucinate metrics. Only use data provided.
- If data isn't available, say: "Hmm, I don't have enough data on that one."
- Keep answers under 150 words.
- Always end with a light follow-up offer like "Want me to dig deeper into any brand?"""

    def detect_brands(q):
        return list(set(
            canonical for alias, canonical in BRAND_ALIASES.items()
            if alias in q.lower()
        ))

    def build_context(brands_mentioned):
        if not brands_mentioned:
            lines = ["OVERVIEW OF ALL BRANDS:\n"]
            for b, d in summary.items():
                lines.append(
                    f"{b}: sentiment={d['sentiment']['avg_weighted_polarity']} | "
                    f"price=₹{d['pricing']['avg_price']} | "
                    f"rating={d['ratings']['avg_star_rating']} | "
                    f"vfm={d['value_for_money'].get('vfm_score_normalized')}/100 | "
                    f"praise={d['themes']['top_praise'][:3]} | "
                    f"complaints={d['themes']['top_complaints'][:3]}"
                )
            lines.append("\nKEY INSIGHTS:\n" + "\n".join(f"- {ins['title']}" for ins in insights))
            return "\n".join(lines)

        lines = []
        for b in brands_mentioned:
            if b not in summary:
                continue
            d = summary[b]
            lines.append(f"""
BRAND: {b}
  Sentiment: {d['sentiment']['avg_weighted_polarity']} | positive={d['sentiment']['positive_pct']}% | negative={d['sentiment']['negative_pct']}%
  Price: ₹{d['pricing']['avg_price']} | discount={d['pricing']['avg_discount_pct']}%
  Rating: {d['ratings']['avg_star_rating']} stars | {d['sentiment']['total_reviews']} reviews
  Aspects: {json.dumps(d['aspects'])}
  VFM: {d['value_for_money'].get('vfm_score_normalized')}/100
  Praise: {d['themes']['top_praise'][:5]}
  Complaints: {d['themes']['top_complaints'][:5]}
  Anomalies: {[a['description'] for a in d['anomalies']]}
""")
        return "\n".join(lines)

    # ── Chat history display ──────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class='chat-message chat-user'>
                <div class='chat-label'>You</div>
                {msg['content']}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='chat-message chat-agent'>
                <div class='chat-label'>🤖 Agent</div>
                {msg['content']}
            </div>""", unsafe_allow_html=True)

    # ── Input form ────────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "question",
                placeholder      = "e.g. Which brand has the worst zipper quality?",
                label_visibility = "collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_input.strip():
        brands_mentioned = detect_brands(user_input)
        context          = build_context(brands_mentioned)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in st.session_state.chat_history[-12:]:
            content = f"Context:\n{context}\n\nQuestion: {m['content']}" if m["role"] == "user" else m["content"]
            api_messages.append({"role": m["role"], "content": content})

        with st.spinner("Thinking..."):
            try:
                resp  = groq_client.chat.completions.create(
                    model       = "llama-3.1-8b-instant",
                    messages    = api_messages,
                    temperature = 0.2,
                    max_tokens  = 300,
                )
                reply = resp.choices[0].message.content.strip()
            except Exception as e:
                reply = f"Error: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("Clear chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
