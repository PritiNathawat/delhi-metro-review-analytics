
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------

st.set_page_config(
    page_title="Delhi Metro Review Analytics",
    page_icon="🚇",
    layout="wide"
)

st.title("🚇 Delhi Metro Sarthi")
st.subheader("Customer Review Analytics Dashboard")
st.caption("Analysis of 3,000 Google Play Store reviews")

# -------------------------------
# 2. LOAD DATA
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed_reviews.csv"

@st.cache_data
def load_data(path):
    return pd.read_csv(path)

if not DATA_PATH.exists():
    st.error(f"Dataset not found: {DATA_PATH}")
    st.stop()

df = load_data(str(DATA_PATH))

# Check required columns
required_columns = ["score", "content"]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# Clean data types
df["score"] = pd.to_numeric(df["score"], errors="coerce")
df = df.dropna(subset=["score", "content"]).copy()
df["score"] = df["score"].astype(int)

# -------------------------------
# 3. SIDEBAR
# -------------------------------

st.sidebar.title("Dashboard Filters")

selected_ratings = st.sidebar.multiselect(
    "Select star ratings",
    options=[1, 2, 3, 4, 5],
    default=[1, 2, 3, 4, 5]
)

if "sentiment" in df.columns:
    sentiments = sorted(df["sentiment"].dropna().unique())

    selected_sentiments = st.sidebar.multiselect(
        "Select sentiment",
        options=sentiments,
        default=sentiments
    )
else:
    selected_sentiments = []

filtered_df = df[df["score"].isin(selected_ratings)].copy()

if "sentiment" in df.columns:
    filtered_df = filtered_df[
        filtered_df["sentiment"].isin(selected_sentiments)
    ]

# -------------------------------
# 4. KEY PERFORMANCE INDICATORS
# -------------------------------

st.markdown("## Overview")

col1, col2, col3, col4 = st.columns(4)

total_reviews = len(filtered_df)
average_rating = filtered_df["score"].mean() if total_reviews else 0

negative_pct = (
    filtered_df["score"].isin([1, 2]).mean() * 100
    if total_reviews else 0
)

positive_pct = (
    filtered_df["score"].isin([4, 5]).mean() * 100
    if total_reviews else 0
)

with col1:
    st.metric("Total Reviews", f"{total_reviews:,}")

with col2:
    st.metric("Average Rating", f"{average_rating:.2f}/5")

with col3:
    st.metric("Negative Ratings", f"{negative_pct:.1f}%")

with col4:
    st.metric("Positive Ratings", f"{positive_pct:.1f}%")

st.divider()

# -------------------------------
# 5. RATING ANALYSIS
# -------------------------------

st.markdown("## ⭐ Rating Analysis")

col1, col2 = st.columns(2)

with col1:
    rating_counts = (
        filtered_df["score"]
        .value_counts()
        .reindex([1, 2, 3, 4, 5], fill_value=0)
        .rename_axis("Rating")
        .reset_index(name="Reviews")
    )

    fig = px.bar(
        rating_counts,
        x="Rating",
        y="Reviews",
        text="Reviews",
        title="Star Rating Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    rating_percentage = (
        rating_counts.assign(
            Percentage=lambda x: (
                x["Reviews"] / max(total_reviews, 1) * 100
            )
        )
    )

    fig = px.pie(
        rating_percentage,
        names="Rating",
        values="Reviews",
        hole=0.45,
        title="Rating Share"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 6. SENTIMENT ANALYSIS
# -------------------------------

if "sentiment" in filtered_df.columns:

    st.divider()
    st.markdown("## 💬 Sentiment Analysis")

    sentiment_counts = (
        filtered_df["sentiment"]
        .value_counts()
        .rename_axis("Sentiment")
        .reset_index(name="Reviews")
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(
            sentiment_counts,
            names="Sentiment",
            values="Reviews",
            hole=0.45,
            title="Sentiment Distribution"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            sentiment_counts,
            x="Sentiment",
            y="Reviews",
            text="Reviews",
            title="Reviews by Sentiment"
        )

        st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 7. TOPIC ANALYSIS
# -------------------------------

st.divider()
st.markdown("## 📌 Review Topic Analysis")

topic_columns = {
    "Payment Failure": "payment_failure",
    "Recharge Issues": "recharge_issues",
    "Virtual Card": "virtual_card",
    "Smart Card": "smart_card",
    "QR Ticketing": "qr_ticketing",
    "App Performance": "app_performance",
    "Balance Issues": "balance_issues",
    "General Experience": "general_experience",
    "Server Issues": "server_issues",
    "Transaction History": "transaction_history",
    "Compatibility Issues": "compatibility_issues",
    "Map and Navigation": "map_and_navigation",
    "Usability and Features": "usability_and_features"
}

available_topics = {
    name: column
    for name, column in topic_columns.items()
    if column in filtered_df.columns
}

if available_topics:

    topic_data = []

    for name, column in available_topics.items():

        matched = filtered_df[
            filtered_df[column].fillna(False).astype(bool)
        ]

        topic_data.append({
            "Topic": name,
            "Reviews": len(matched),
            "Average Rating": (
                round(matched["score"].mean(), 2)
                if len(matched) else 0
            )
        })

    topic_df = pd.DataFrame(topic_data)
    topic_df = topic_df.sort_values("Reviews", ascending=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            topic_df,
            x="Reviews",
            y="Topic",
            orientation="h",
            text="Reviews",
            title="Reviews by Topic"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            topic_df,
            x="Average Rating",
            y="Topic",
            orientation="h",
            title="Average Rating by Topic"
        )

        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No topic columns found in the dataset.")

# -------------------------------
# 8. MONTHLY TREND
# -------------------------------

st.divider()
st.markdown("## 📅 Monthly Review Trends")

if "month" in filtered_df.columns:

    monthly_df = filtered_df.copy()

    monthly_df["month_date"] = pd.to_datetime(
        monthly_df["month"],
        errors="coerce"
    )

    monthly_df = monthly_df.dropna(subset=["month_date"])

    if not monthly_df.empty:

        monthly_summary = (
            monthly_df.groupby("month_date")
            .agg(
                Average_Rating=("score", "mean"),
                Review_Count=("score", "size")
            )
            .reset_index()
            .sort_values("month_date")
        )

        fig = px.line(
            monthly_summary,
            x="month_date",
            y="Average_Rating",
            markers=True,
            title="Average Monthly Rating"
        )

        fig.update_yaxes(range=[0, 5])

        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(
            monthly_summary,
            x="month_date",
            y="Review_Count",
            title="Monthly Review Volume"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Monthly dates could not be interpreted.")

else:
    st.info("Month column not found.")

# -------------------------------
# 9. REVIEW EXPLORER
# -------------------------------

st.divider()
st.markdown("## 🔍 Explore Customer Reviews")

search_text = st.text_input(
    "Search reviews",
    placeholder="Search for card, recharge, QR code, payment..."
)

review_df = filtered_df.copy()

if search_text:
    review_df = review_df[
        review_df["content"].str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

display_columns = [
    col for col in [
        "score",
        "content",
        "sentiment",
        "thumbsUpCount",
        "at"
    ]
    if col in review_df.columns
]

st.write(f"Matching reviews: {len(review_df)}")

st.dataframe(
    review_df[display_columns].head(100),
    use_container_width=True,
    hide_index=True
)

# -------------------------------
# 10. FOOTER
# -------------------------------

st.divider()

st.caption(
    "Delhi Metro Sarthi Review Analytics | "
    "Data source: Google Play Store reviews | "
    "Sentiment analysis: VADER baseline"
)
