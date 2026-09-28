"""
India Air Quality Dashboard — Streamlit app
Run:
    pip install -r requirements.txt
    streamlit run app.py

Dataset: India Air Quality Dataset (2025–2026)
"""

import glob
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="India Air Quality Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---------- Global ---------- */
    .stApp {
        background: #f6f8fb;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #172033 100%);
        border-right: 1px solid #263247;
    }

    section[data-testid="stSidebar"] * {
        color: #f8fafc;
    }

    section[data-testid="stSidebar"] label {
        font-weight: 600;
    }

    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.06);
        border: 1px dashed #64748b;
        border-radius: 12px;
        padding: 8px;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div {
        background: #202b3f;
        border: 1px solid #3b4a63;
        border-radius: 10px;
    }

    /* ---------- Dashboard header ---------- */
    .dashboard-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        padding: 28px 32px;
        border-radius: 18px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
    }

    .dashboard-header h1 {
        color: white;
        margin: 0;
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .dashboard-header p {
        color: #cbd5e1;
        margin: 8px 0 0;
        font-size: 1rem;
    }

    /* ---------- Section headings ---------- */
    .section-title {
        color: #0f172a;
        font-size: 1.35rem;
        font-weight: 800;
        margin: 18px 0 12px;
        padding-left: 12px;
        border-left: 5px solid #2563eb;
    }

    /* ---------- KPI cards ---------- */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 5px 18px rgba(15, 23, 42, 0.06);
        min-height: 110px;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 800;
    }

    /* ---------- Tables ---------- */
    div[data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.04);
    }

    /* ---------- Alerts ---------- */
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* ---------- Buttons ---------- */
    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
    }

    /* ---------- Dividers ---------- */
    hr {
        margin: 1.5rem 0;
        border-color: #e2e8f0;
    }

    /* ---------- Small info cards ---------- */
    .info-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
    }

    .info-card-title {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }

    .info-card-value {
        font-size: 1.45rem;
        color: #0f172a;
        font-weight: 800;
        margin-top: 4px;
    }

    /* ---------- Footer ---------- */
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        padding: 28px 0 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="padding: 12px 0 18px; border-bottom: 1px solid rgba(255,255,255,0.18); margin-bottom: 16px;">
        <div style="font-size: 1.4rem; font-weight: 800; color:#ffffff; letter-spacing:0.2px;">🌫️ Air Quality</div>
        <div style="color:#bfdbfe; font-size:0.9rem; font-weight:600; margin-top:6px; letter-spacing:0.3px;">
            Dashboard Filters
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv(file_or_path):
    return pd.read_csv(file_or_path)


csv_candidates = glob.glob("*.csv")
df_raw = None

if csv_candidates:
    df_raw = load_csv(csv_candidates[0])
else:
    uploaded = st.sidebar.file_uploader(
        "Upload the dataset CSV",
        type="csv",
    )
    if uploaded is not None:
        df_raw = load_csv(uploaded)

if df_raw is None:
    st.markdown(
        """
        <div class="dashboard-header">
            <h1>🌫️ India Air Quality Dashboard</h1>
            <p>Explore air-quality data, pollutants, trends and AQI patterns.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "No CSV found in this folder, and nothing uploaded yet.\n\n"
        "Download the dataset and either:\n"
        "1. Place the CSV next to `app.py`, or\n"
        "2. Upload the CSV using the sidebar."
    )
    st.stop()

# ---------------------------------------------------------------------
# 2. AUTO-DETECT IMPORTANT COLUMNS
# ---------------------------------------------------------------------
def find_col(candidates, columns):
    cols_lower = {str(c).lower(): c for c in columns}

    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]

    for c in columns:
        for cand in candidates:
            if cand.lower() in str(c).lower():
                return c

    return None


cols = list(df_raw.columns)

COLMAP = {
    "state": find_col(["state", "region"], cols),
    "city": find_col(["city", "location", "station", "area"], cols),
    "date": find_col(["date", "datetime", "timestamp", "day"], cols),
    "aqi": find_col(["aqi", "air quality index", "aqi_value"], cols),
    "bucket": find_col(
        ["aqi_bucket", "bucket", "category", "aqi_category"], cols
    ),
    "pm25": find_col(["pm2.5", "pm25", "pm_2.5"], cols),
    "pm10": find_col(["pm10", "pm_10"], cols),
    "no2": find_col(["no2"], cols),
    "so2": find_col(["so2"], cols),
    "co": find_col(["co"], cols),
    "o3": find_col(["o3", "ozone"], cols),
    "nh3": find_col(["nh3"], cols),
}

# If auto-detection chooses the wrong column, set it manually here.
# Example:
# COLMAP["aqi"] = "AQI_Value"
# COLMAP["state"] = "State"

df = df_raw.copy()

# ---------------------------------------------------------------------
# 3. CLEAN NUMERIC COLUMNS
# ---------------------------------------------------------------------
numeric_keys = [
    "aqi",
    "pm25",
    "pm10",
    "no2",
    "so2",
    "co",
    "o3",
    "nh3",
]

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


# ---------------------------------------------------------------------
# 4. PARSE DATE SAFELY
# ---------------------------------------------------------------------
if COLMAP["date"]:
    date_col = COLMAP["date"]

    parsed_default = pd.to_datetime(
        df[date_col],
        errors="coerce",
    )

    parsed_dayfirst = pd.to_datetime(
        df[date_col],
        errors="coerce",
        dayfirst=True,
    )

    parsed = (
        parsed_default
        if parsed_default.notna().sum() >= parsed_dayfirst.notna().sum()
        else parsed_dayfirst
    )

    if parsed.notna().mean() < 0.5:
        COLMAP["date"] = None
    else:
        df[date_col] = parsed
        df = df.dropna(subset=[date_col])


# ---------------------------------------------------------------------
# 5. CREATE AQI CATEGORY IF NEEDED
# ---------------------------------------------------------------------
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

POLLUTANTS = [
    COLMAP[k]
    for k in numeric_keys
    if COLMAP[k] is not None
]

if not LOCATION_COL or not POLLUTANTS:
    st.error(
        "Couldn't confidently detect a location column or numeric pollutant columns. "
        "Open app.py and set the COLMAP overrides manually. "
        f"Available columns: {cols}"
    )
    st.stop()

# ---------------------------------------------------------------------
# 6. SIDEBAR FILTERS
# ---------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div style="font-size:1rem;font-weight:800;margin-bottom:8px;">📍 Location</div>',
    unsafe_allow_html=True,
)

all_locations = sorted(
    df[LOCATION_COL].dropna().unique().tolist(),
    key=lambda x: str(x),
)

selected_locations = st.sidebar.multiselect(
    f"Select {LOCATION_COL}",
    options=all_locations,
    default=all_locations[:10] if len(all_locations) > 10 else all_locations,
)

st.sidebar.markdown(
    '<div style="font-size:1rem;font-weight:800;margin:18px 0 8px;">📊 Metric</div>',
    unsafe_allow_html=True,
)

metric = st.sidebar.selectbox(
    "Choose pollutant / AQI",
    options=POLLUTANTS,
    index=0,
)

# ---------------------------------------------------------------------
# 7. DATE SLIDER — FIXED VERSION
# ---------------------------------------------------------------------
date_range = None

if COLMAP["date"]:
    date_col = COLMAP["date"]
    valid_dates = df[date_col].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        st.sidebar.markdown(
            '<div style="font-size:1rem;font-weight:800;margin:18px 0 8px;">📅 Period</div>',
            unsafe_allow_html=True,
        )

        if min_date < max_date:
            date_range = st.sidebar.slider(
                "Select date range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="DD/MM/YYYY",
            )
        else:
            st.sidebar.caption(
                f"{min_date.strftime('%d/%m/%Y')} "
                "(only one date in data — filter disabled)"
            )

# ---------------------------------------------------------------------
# 8. APPLY FILTERS
# ---------------------------------------------------------------------
if selected_locations:
    fdf = df[df[LOCATION_COL].isin(selected_locations)].copy()
else:
    fdf = df.copy()

if date_range and COLMAP["date"]:
    date_col = COLMAP["date"]
    start_date, end_date = date_range

    row_dates = df[date_col].dt.date

    fdf = fdf[
        (row_dates.loc[fdf.index] >= start_date)
        & (row_dates.loc[fdf.index] <= end_date)
    ]

if fdf.empty:
    st.warning("No data for this selection — widen your filters.")
    st.stop()

# ---------------------------------------------------------------------
# 9. MAIN HEADER
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="dashboard-header">
        <h1>🌫️ India Air Quality Dashboard</h1>
        <p>
            Explore AQI, pollutant levels, geographical patterns and
            air-quality trends from the selected dataset.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# 10. KPI SECTION
# ---------------------------------------------------------------------
st.markdown(
    '<div class="section-title">📌 Dashboard Overview</div>',
    unsafe_allow_html=True,
)

c0, c1 = st.columns(2)

c0.metric(
    "Readings in selection",
    f"{len(fdf):,}",
)

c1.metric(
    "Locations selected",
    f"{fdf[LOCATION_COL].nunique():,}",
)

for row_start in range(0, len(POLLUTANTS), 4):
    row_metrics = POLLUTANTS[row_start:row_start + 4]
    kpi_cols = st.columns(len(row_metrics))

    for c, m in zip(kpi_cols, row_metrics):
        avg_value = fdf[m].mean()

        c.metric(
            f"Average {m}",
            f"{avg_value:,.1f}" if pd.notna(avg_value) else "N/A",
        )

# ---------------------------------------------------------------------
# 11. SUMMARY STATISTICS
# ---------------------------------------------------------------------
st.markdown(
    '<div class="section-title">📈 Summary Statistics</div>',
    unsafe_allow_html=True,
)

summary = (
    fdf[POLLUTANTS]
    .agg(["min", "median", "mean", "max", "std"])
    .T
)

summary.columns = [
    "Min",
    "Median",
    "Mean",
    "Max",
    "Std Dev",
]

st.dataframe(
    summary.round(2),
    use_container_width=True,
)

# ---------------------------------------------------------------------
# 12. FILTERED DATA
# ---------------------------------------------------------------------
st.markdown(
    '<div class="section-title">🗂️ Filtered Data</div>',
    unsafe_allow_html=True,
)

show_cols = [
    c
    for c in [
        LOCATION_COL,
        COLMAP.get("city") if COLMAP.get("state") else None,
        COLMAP["date"],
    ] + POLLUTANTS
    if c
]

show_cols = list(dict.fromkeys(show_cols))

st.dataframe(
    fdf[show_cols].reset_index(drop=True),
    use_container_width=True,
)

# ---------------------------------------------------------------------
# 13. CHARTS
# ---------------------------------------------------------------------
st.markdown(
    '<div class="section-title">📊 Visual Analysis</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

# ----- Bar chart -----
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

    fig_bar.update_layout(
        template="plotly_white",
        xaxis_tickangle=-45,
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=18),
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True,
    )

# ----- Pie chart -----
with col2:
    if COLMAP["bucket"] and COLMAP["bucket"] in fdf.columns:
        pie_data = (
            fdf[COLMAP["bucket"]]
            .value_counts()
            .reset_index()
        )

        pie_data.columns = ["bucket", "count"]

        fig_pie = px.pie(
            pie_data,
            names="bucket",
            values="count",
            title="Share of Readings by AQI Category",
            hole=0.35,
        )
    else:
        fig_pie = px.pie(
            bar_data,
            names=LOCATION_COL,
            values=metric,
            title=f"Share of {metric} by {LOCATION_COL}",
            hole=0.35,
        )

    fig_pie.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=18),
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True,
    )

# ---------------------------------------------------------------------
# 14. TREND OVER TIME
# ---------------------------------------------------------------------
if COLMAP["date"]:
    st.markdown(
        '<div class="section-title">📅 Trend Over Time</div>',
        unsafe_allow_html=True,
    )

    trend = (
        fdf.groupby(
            fdf[COLMAP["date"]].dt.to_period("M")
        )[metric]
        .mean()
        .reset_index()
    )

    trend[COLMAP["date"]] = trend[COLMAP["date"]].dt.to_timestamp()

    fig_line = px.line(
        trend,
        x=COLMAP["date"],
        y=metric,
        markers=True,
        title=f"{metric} Trend Over Time",
    )

    fig_line.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=18),
    )

    st.plotly_chart(
        fig_line,
        use_container_width=True,
    )

# ---------------------------------------------------------------------
# 15. DISTRIBUTION + BOX PLOT
# ---------------------------------------------------------------------
st.markdown(
    '<div class="section-title">🔎 Detailed Analysis</div>',
    unsafe_allow_html=True,
)

col3, col4 = st.columns(2)

# ----- Histogram -----
with col3:
    fig_hist = px.histogram(
        fdf,
        x=metric,
        nbins=40,
        marginal="box",
        title=f"Distribution of {metric}",
    )

    fig_hist.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=18),
    )

    st.plotly_chart(
        fig_hist,
        use_container_width=True,
    )

# ----- Box plot -----
with col4:
    top_locations = (
        fdf.groupby(LOCATION_COL)[metric]
        .mean()
        .sort_values(ascending=False)
        .head(15)
        .index
    )

    fig_box = px.box(
        fdf[fdf[LOCATION_COL].isin(top_locations)],
        x=LOCATION_COL,
        y=metric,
        color=LOCATION_COL,
        title=f"{metric} Spread — Top 15 {LOCATION_COL}s",
    )

    fig_box.update_layout(
        template="plotly_white",
        showlegend=False,
        xaxis_tickangle=-45,
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=18),
    )

    st.plotly_chart(
        fig_box,
        use_container_width=True,
    )

# ---------------------------------------------------------------------
# 16. CORRELATION HEATMAP
# ---------------------------------------------------------------------
if len(POLLUTANTS) > 1:
    st.markdown(
        '<div class="section-title">🔗 Pollutant Correlation</div>',
        unsafe_allow_html=True,
    )

    corr = fdf[POLLUTANTS].corr(numeric_only=True)

    fig_corr = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        title="Correlation Between Pollutants",
    )

    fig_corr.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        title_font=dict(size=18),
    )

    st.plotly_chart(
        fig_corr,
        use_container_width=True,
    )

# ---------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        🌫️ India Air Quality Dashboard &nbsp;•&nbsp;
        Interactive data exploration with Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
