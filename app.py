"""
India Air Quality Dashboard — Streamlit app
Run locally with:
    pip install -r requirements.txt
    streamlit run app.py

Dataset: India Air Quality Dataset (2025–2026)
https://www.kaggle.com/datasets/yogeshm01/india-air-quality-dataset-20252026

Put the dataset CSV in the same folder as this script (or use the
file-uploader that appears if no CSV is found), then run the command above.
"""

import glob
import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="India Air Quality Dashboard", layout="wide")

# ---------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------
st.sidebar.title("Dashboard Filters")


@st.cache_data
def load_csv(file_or_path):
    return pd.read_csv(file_or_path)


csv_candidates = glob.glob("*.csv")
df_raw = None

if csv_candidates:
    df_raw = load_csv(csv_candidates[0])
else:
    uploaded = st.sidebar.file_uploader("Upload the dataset CSV", type="csv")
    if uploaded is not None:
        df_raw = load_csv(uploaded)

if df_raw is None:
    st.title("India Air Quality Dashboard")
    st.info(
        "No CSV found in this folder, and nothing uploaded yet.\n\n"
        "Download the dataset from Kaggle and either:\n"
        "1. Place the CSV file next to `app.py` and rerun, or\n"
        "2. Use the uploader in the sidebar."
    )
    st.stop()

# ---------------------------------------------------------------------
# 2. Auto-detect key columns (edit COLMAP manually below if it guesses wrong)
# ---------------------------------------------------------------------


def find_col(candidates, columns):
    cols_lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    for c in columns:
        for cand in candidates:
            if cand.lower() in c.lower():
                return c
    return None


cols = list(df_raw.columns)

COLMAP = {
    "state": find_col(["state", "region"], cols),
    "city": find_col(["city", "location", "station", "area"], cols),
    "date": find_col(["date", "datetime", "timestamp", "day"], cols),
    "aqi": find_col(["aqi", "air quality index", "aqi_value"], cols),
    "bucket": find_col(["aqi_bucket", "bucket", "category", "aqi_category"], cols),
    "pm25": find_col(["pm2.5", "pm25", "pm_2.5"], cols),
    "pm10": find_col(["pm10", "pm_10"], cols),
    "no2": find_col(["no2"], cols),
    "so2": find_col(["so2"], cols),
    "co": find_col(["co"], cols),
    "o3": find_col(["o3", "ozone"], cols),
    "nh3": find_col(["nh3"], cols),
}

# --- OVERRIDE HERE if auto-detection picks the wrong column, e.g.:
# COLMAP["aqi"] = "AQI_Value"
# COLMAP["state"] = "State"

df = df_raw.copy()

# Force pollutant/AQI columns to numeric, dropping ones that never work
numeric_keys = ["aqi", "pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
for key in numeric_keys:
    col = COLMAP[key]
    if col is None:
        continue
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"(-?\d+\.?\d*)")[0]
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[col].notna().sum() == 0:
        COLMAP[key] = None

# Parse date column defensively
if COLMAP["date"]:
    parsed_default = pd.to_datetime(df[COLMAP["date"]], errors="coerce")
    parsed_dayfirst = pd.to_datetime(df[COLMAP["date"]], errors="coerce", dayfirst=True)
    parsed = (
        parsed_default
        if parsed_default.notna().sum() >= parsed_dayfirst.notna().sum()
        else parsed_dayfirst
    )
    if parsed.notna().mean() < 0.5:
        COLMAP["date"] = None
    else:
        df[COLMAP["date"]] = parsed
        df = df.dropna(subset=[COLMAP["date"]])


def aqi_bucket(v):
    if pd.isna(v):
        return None
    if v <= 50:
        return "Good"
    if v <= 100:
        return "Satisfactory"
    if v <= 200:
        return "Moderate"
    if v <= 300:
        return "Poor"
    if v <= 400:
        return "Very Poor"
    return "Severe"


if COLMAP["bucket"] is None and COLMAP["aqi"] is not None:
    df["AQI_Bucket"] = df[COLMAP["aqi"]].apply(aqi_bucket)
    COLMAP["bucket"] = "AQI_Bucket"

LOCATION_COL = COLMAP["state"] or COLMAP["city"]
if LOCATION_COL:
    df = df.dropna(subset=[LOCATION_COL])

POLLUTANTS = [COLMAP[k] for k in numeric_keys if COLMAP[k] is not None]

if not LOCATION_COL or not POLLUTANTS:
    st.error(
        "Couldn't confidently detect a location column or any numeric pollutant columns. "
        "Open app.py and set the COLMAP overrides manually near the top of the file, "
        f"using one of these column names: {cols}"
    )
    st.stop()

# ---------------------------------------------------------------------
# 3. Sidebar filters
# ---------------------------------------------------------------------
all_locations = sorted(df[LOCATION_COL].dropna().unique().tolist())

st.sidebar.subheader(f"Select {LOCATION_COL}")
selected_locations = st.sidebar.multiselect(
    "Select",
    options=all_locations,
    default=all_locations[:10] if len(all_locations) > 10 else all_locations,
)

metric = st.sidebar.selectbox("Metric", options=POLLUTANTS, index=0)

date_range = None
if COLMAP["date"]:
    date_col = COLMAP["date"]

    # Use plain Python dates for the Streamlit slider.
    # This avoids StreamlitInvalidMinMaxError caused by datetime/timezone
    # values or datasets containing only one unique day.
    valid_dates = df[date_col].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        if min_date < max_date:
            date_range = st.sidebar.slider(
                "Period",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="DD/MM/YYYY",
            )
        else:
            st.sidebar.caption(
                f"Period: {min_date.strftime('%d/%m/%Y')} "
                "(only one date in data — filter disabled)"
            )

fdf = df[df[LOCATION_COL].isin(selected_locations)] if selected_locations else df.copy()
if date_range and COLMAP["date"]:
    date_col = COLMAP["date"]
    start_date, end_date = date_range

    # Compare by calendar date, not timestamp/time-of-day.
    row_dates = df[date_col].dt.date
    fdf = fdf[(row_dates.loc[fdf.index] >= start_date) &
              (row_dates.loc[fdf.index] <= end_date)]

# ---------------------------------------------------------------------
# 4. Main panel
# ---------------------------------------------------------------------
st.markdown("# explore the insights here 👇")

if fdf.empty:
    st.warning("No data for this selection — widen your filters.")
    st.stop()

# KPI cards — one row per group of 4, covering every pollutant column (not just the first four)
c0, c1 = st.columns(2)
c0.metric("Readings in selection", f"{len(fdf):,}")
c1.metric(f"Locations selected", f"{fdf[LOCATION_COL].nunique():,}")

for row_start in range(0, len(POLLUTANTS), 4):
    row_metrics = POLLUTANTS[row_start:row_start + 4]
    kpi_cols = st.columns(len(row_metrics))
    for c, m in zip(kpi_cols, row_metrics):
        c.metric(f"Average {m}", f"{fdf[m].mean():,.1f}")

st.divider()

# Summary statistics table — min / median / mean / max / std for every pollutant
st.subheader("Summary statistics")
summary = fdf[POLLUTANTS].agg(["min", "median", "mean", "max", "std"]).T
summary.columns = ["Min", "Median", "Mean", "Max", "Std Dev"]
st.dataframe(summary.round(2), use_container_width=True)

st.divider()

# Data table
show_cols = [c for c in [LOCATION_COL, COLMAP.get("city") if COLMAP.get("state") else None,
                         COLMAP["date"]] + POLLUTANTS if c]
show_cols = list(dict.fromkeys(show_cols))  # dedupe, keep order
st.subheader("Filtered data")
st.dataframe(fdf[show_cols].reset_index(drop=True), use_container_width=True)

col1, col2 = st.columns(2)

# Bar chart
with col1:
    bar_data = (
        fdf.groupby(LOCATION_COL, as_index=False)[metric]
        .mean()
        .sort_values(metric, ascending=False)
    )
    fig_bar = px.bar(
        bar_data,
        x=LOCATION_COL,
        y=metric,
        color=metric,
        color_continuous_scale="Plasma",
        title=f"Average {metric} by {LOCATION_COL}",
    )
    fig_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)

# Pie chart
with col2:
    if COLMAP["bucket"] and COLMAP["bucket"] in fdf.columns:
        pie_data = fdf[COLMAP["bucket"]].value_counts().reset_index()
        pie_data.columns = ["bucket", "count"]
        fig_pie = px.pie(
            pie_data, names="bucket", values="count",
            title="Share of readings by AQI category", hole=0.35,
        )
    else:
        fig_pie = px.pie(
            bar_data, names=LOCATION_COL, values=metric,
            title=f"Share of {metric} by {LOCATION_COL}", hole=0.35,
        )
    st.plotly_chart(fig_pie, use_container_width=True)

# Line chart — trend over time
if COLMAP["date"]:
    trend = (
        fdf.groupby(fdf[COLMAP["date"]].dt.to_period("M"))[metric]
        .mean()
        .reset_index()
    )
    trend[COLMAP["date"]] = trend[COLMAP["date"]].dt.to_timestamp()
    fig_line = px.line(
        trend, x=COLMAP["date"], y=metric, markers=True,
        title=f"{metric} trend over time",
    )
    st.plotly_chart(fig_line, use_container_width=True)

col3, col4 = st.columns(2)

# Distribution — histogram of the selected metric
with col3:
    fig_hist = px.histogram(
        fdf, x=metric, nbins=40, marginal="box",
        title=f"Distribution of {metric}",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# Spread by location — box plot
with col4:
    top_locations = (
        fdf.groupby(LOCATION_COL)[metric].mean().sort_values(ascending=False).head(15).index
    )
    fig_box = px.box(
        fdf[fdf[LOCATION_COL].isin(top_locations)],
        x=LOCATION_COL, y=metric, color=LOCATION_COL,
        title=f"{metric} spread — top 15 {LOCATION_COL}s by average",
    )
    fig_box.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_box, use_container_width=True)

# Correlation heatmap across all detected pollutants
if len(POLLUTANTS) > 1:
    st.divider()
    st.subheader("Correlation between pollutants")
    corr = fdf[POLLUTANTS].corr(numeric_only=True)
    fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r")
    st.plotly_chart(fig_corr, use_container_width=True)
