CSS = '<style>\n.stApp{background:#f3f6fa}.main .block-container{padding-top:2rem;padding-bottom:3rem;max-width:1450px}\nsection[data-testid="stSidebar"]{background:linear-gradient(180deg,#17324d 0%,#214766 100%);border-right:1px solid #cbd5e1;color:#f8fafc}\nsection[data-testid="stSidebar"] label{color:#f8fafc!important;font-weight:600}\nsection[data-testid="stSidebar"] [data-testid="stFileUploader"]{background:#fff;border:1px solid #d7e2ee;border-radius:11px;padding:10px}\nsection[data-testid="stSidebar"] [data-testid="stFileUploader"] *{color:#1e293b!important}\nsection[data-testid="stSidebar"] [data-testid="stFileUploader"] button{color:#173b63!important;border:1px solid #b9c9da;background:#f8fbff}\nsection[data-testid="stSidebar"] [data-baseweb="select"]>div,section[data-testid="stSidebar"] [data-baseweb="input"]>div{background:#fff!important;color:#1e293b!important;border:1px solid #cbd5e1;border-radius:9px}\nsection[data-testid="stSidebar"] [data-baseweb="select"] *,section[data-testid="stSidebar"] [data-baseweb="input"] *{color:#1e293b!important}\nsection[data-testid="stSidebar"] [data-baseweb="tag"]{background:#e8f1fb!important;border:1px solid #bfd2e6!important}\nsection[data-testid="stSidebar"] [data-baseweb="tag"] span{color:#173b63!important}\nsection[data-testid="stSidebar"] [data-testid="stSlider"] *{color:#f8fafc!important}\nsection[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#dbe7f2!important}\n.dashboard-header{background:linear-gradient(135deg,#dbeafe 0%,#eef6ff 55%,#f8fafc 100%);border:1px solid #bfdbfe;padding:28px 32px;border-radius:16px;margin-bottom:24px;box-shadow:0 8px 24px rgba(30,64,175,.09)}\n.dashboard-header h1{color:#173b63;margin:0;font-size:2.15rem;font-weight:800}.dashboard-header p{color:#475569;margin:8px 0 0}\n.section-title{color:#1e3a5f;font-size:1.3rem;font-weight:800;margin:20px 0 12px;padding:10px 14px;border-left:4px solid #3b82f6;background:#fff;border-radius:0 9px 9px 0;box-shadow:0 2px 8px rgba(15,23,42,.04)}\ndiv[data-testid="stMetric"]{background:#fff;border:1px solid #dbe4ee;border-radius:13px;padding:16px 18px;box-shadow:0 5px 16px rgba(15,23,42,.06);min-height:105px}\ndiv[data-testid="stMetricLabel"]{color:#64748b!important;font-weight:600}div[data-testid="stMetricValue"]{color:#173b63!important;font-weight:800}\ndiv[data-testid="stDataFrame"]{border:1px solid #dbe4ee;border-radius:11px;overflow:hidden;box-shadow:0 4px 14px rgba(15,23,42,.04)}\n.footer{text-align:center;color:#64748b;font-size:.85rem;padding:28px 0 8px}\n</style>'

import glob
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="India Air Quality Dashboard", page_icon="🌫️", layout="wide", initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="padding:10px 0 18px;border-bottom:1px solid rgba(255,255,255,.18);margin-bottom:14px;">
<div style="font-size:1.35rem;font-weight:800;color:#ffffff;">🌫️ Air Quality</div>
<div style="color:#bfdbfe!important;font-size:.9rem;font-weight:600;margin-top:5px;">Dashboard Filters</div>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_csv(path_or_file):
    return pd.read_csv(path_or_file)

files = glob.glob("*.csv")
df_raw = None
if files:
    preferred = next((x for x in files if "enriched_aqi_dataset" in x.lower()), files[0])
    df_raw = load_csv(preferred)
else:
    uploaded = st.sidebar.file_uploader("Upload the dataset CSV", type="csv")
    if uploaded is not None:
        df_raw = load_csv(uploaded)

if df_raw is None:
    st.markdown('<div class="dashboard-header"><h1>🌫️ India Air Quality Dashboard</h1><p>Explore air-quality data, pollutants, trends and AQI patterns.</p></div>', unsafe_allow_html=True)
    st.info("No CSV found. Put enriched_aqi_dataset.csv next to app.py or upload a CSV from the sidebar.")
    st.stop()

required = ["last_update","state","city","station","pollutant_id","pollutant_avg","AQI","AQI_Bucket"]
missing = [c for c in required if c not in df_raw.columns]
if missing:
    st.error("Required columns missing: " + ", ".join(missing))
    st.stop()

df = df_raw.copy()
df["last_update"] = pd.to_datetime(df["last_update"], errors="coerce")
df["pollutant_avg"] = pd.to_numeric(df["pollutant_avg"], errors="coerce")
df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")
df = df.dropna(subset=["last_update"]).copy()

# Project data scope: use only 2025 and 2026 records.
# The uploaded CSV also contains 2027 records, but they are intentionally
# excluded so the Period selector stays within the project's 2025-2026 scope.
df = df[
    (df["last_update"].dt.year >= 2025)
    & (df["last_update"].dt.year <= 2026)
].copy()

df["_date"] = df["last_update"].dt.date

for col in ["state","city","station","pollutant_id","AQI_Bucket"]:
    df[col] = df[col].fillna("Unknown").astype(str)

st.sidebar.markdown('<div style="font-size:1rem;font-weight:800;margin:18px 0 8px;color:#fff;">📍 Location</div>', unsafe_allow_html=True)
states = sorted(df["state"].unique())
selected_states = st.sidebar.multiselect("Select State", states, default=states, key="state_filter")

city_source = df[df["state"].isin(selected_states)] if selected_states else df.iloc[0:0]
cities = sorted(city_source["city"].unique())
selected_cities = st.sidebar.multiselect("Select City", cities, default=cities[:10] if len(cities)>10 else cities, key="city_filter")

st.sidebar.markdown('<div style="font-size:1rem;font-weight:800;margin:18px 0 8px;color:#fff;">📊 Metric</div>', unsafe_allow_html=True)
metric_type = st.sidebar.selectbox("Choose metric", ["AQI", "Pollutant Average"], key="metric_filter")

selected_pollutant = None
if metric_type == "Pollutant Average":
    pollutants = sorted(df["pollutant_id"].unique())
    selected_pollutant = st.sidebar.selectbox("Select pollutant", pollutants, key="pollutant_filter")

# -------------------- WORKING PERIOD FILTER --------------------
st.sidebar.markdown('<div style="font-size:1rem;font-weight:800;margin:18px 0 8px;color:#fff;">📅 Period</div>', unsafe_allow_html=True)

min_date = df["_date"].min()
max_date = df["_date"].max()

if min_date < max_date:
    date_range = st.sidebar.slider(
        "Select date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="DD/MM/YYYY",
        key="period_slider"
    )
else:
    date_range = (min_date, max_date)
    st.sidebar.caption(min_date.strftime("%d/%m/%Y") + " — only one date available")

start_date, end_date = date_range
st.sidebar.markdown(
    '<div style="background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.20);border-radius:8px;padding:8px 10px;margin-top:6px;color:#dbeafe;font-size:.82rem;"><b>Selected Period</b><br>'
    + start_date.strftime("%d/%m/%Y") + " → " + end_date.strftime("%d/%m/%Y")
    + "</div>",
    unsafe_allow_html=True
)

# Apply all filters to the same dataframe.
fdf = df.copy()
if selected_states:
    fdf = fdf[fdf["state"].isin(selected_states)].copy()
if selected_cities:
    fdf = fdf[fdf["city"].isin(selected_cities)].copy()

fdf = fdf[(fdf["_date"] >= start_date) & (fdf["_date"] <= end_date)].copy()

if metric_type == "Pollutant Average":
    fdf = fdf[fdf["pollutant_id"] == selected_pollutant].copy()
    value_col = "pollutant_avg"
    value_label = selected_pollutant + " Average"
else:
    value_col = "AQI"
    value_label = "AQI"

fdf = fdf.dropna(subset=[value_col]).copy()
if fdf.empty:
    st.warning("No data is available for the selected period and location. Please widen the filters.")
    st.stop()

st.markdown('<div class="dashboard-header"><h1>🌫️ India Air Quality Dashboard</h1><p>Explore AQI, pollutant levels, geographical patterns and air-quality trends.</p></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📌 Dashboard Overview</div>', unsafe_allow_html=True)

a,b,c,d = st.columns(4)
a.metric("Readings", f"{len(fdf):,}")
b.metric("States", f"{fdf['state'].nunique():,}")
c.metric("Cities", f"{fdf['city'].nunique():,}")
d.metric(f"Average {value_label}", f"{fdf[value_col].mean():,.1f}")

st.markdown('<div class="section-title">📈 Summary Statistics</div>', unsafe_allow_html=True)
summary = fdf[value_col].agg(["min","median","mean","max","std"]).to_frame("Value")
summary.index = ["Minimum","Median","Mean","Maximum","Std Dev"]
st.dataframe(summary.round(2), use_container_width=True)

st.markdown('<div class="section-title">🗂️ Filtered Data</div>', unsafe_allow_html=True)
display_cols = ["state","city","station","last_update","pollutant_id","pollutant_avg","AQI","AQI_Bucket"]
st.dataframe(fdf[display_cols].sort_values("last_update", ascending=False).reset_index(drop=True), use_container_width=True)

st.markdown('<div class="section-title">📊 Visual Analysis</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)

with c1:
    state_avg = fdf.groupby("state", as_index=False)[value_col].mean().sort_values(value_col, ascending=False)
    fig = px.bar(state_avg, x="state", y=value_col, color=value_col, color_continuous_scale="Blues", title=f"Average {value_label} by State")
    fig.update_layout(template="plotly_white", xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    bucket = fdf["AQI_Bucket"].value_counts().reset_index()
    bucket.columns = ["AQI_Bucket","Count"]
    fig = px.pie(bucket, names="AQI_Bucket", values="Count", hole=.35, title="AQI Category Distribution")
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">📅 Trend Over Time</div>', unsafe_allow_html=True)
trend = fdf.set_index("last_update")[value_col].resample("D").mean().dropna().reset_index()
fig = px.line(trend, x="last_update", y=value_col, markers=True, title=f"{value_label} — Daily Trend")
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">🔎 Detailed Analysis</div>', unsafe_allow_html=True)
c1,c2 = st.columns(2)
with c1:
    fig = px.histogram(fdf, x=value_col, nbins=40, marginal="box", title=f"Distribution of {value_label}")
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    city_avg = fdf.groupby("city", as_index=False)[value_col].mean().sort_values(value_col, ascending=False).head(15)
    fig = px.bar(city_avg, x=value_col, y="city", orientation="h", title=f"Top 15 Cities by Average {value_label}")
    fig.update_layout(template="plotly_white", yaxis={"categoryorder":"total ascending"})
    st.plotly_chart(fig, use_container_width=True)

corr_cols = [c for c in ["AQI","pollutant_avg","Temperature_C","Humidity_%","Wind_Speed_kmh"] if c in fdf.columns]
if len(corr_cols)>1:
    st.markdown('<div class="section-title">🔗 Correlation</div>', unsafe_allow_html=True)
    corr = fdf[corr_cols].corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", title="Environmental & Air Quality Correlation")
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="footer">🌫️ India Air Quality Dashboard &nbsp;•&nbsp; Interactive data exploration with Streamlit</div>', unsafe_allow_html=True)
