import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date, timedelta
import pandas as pd

from core.gee_auth import initialize_gee
from core.change_detection import detect_forest_change
from core.carbon import estimate_carbon_impact
from config.regions import REGIONS, DEFAULT_REGION

# -----------------------------
# GEE Init
# -----------------------------
try:
    initialize_gee()
    gee_ok = True
except Exception as e:
    gee_ok = False
    gee_error = str(e)

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="ForestWatch AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; }

[data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #080f0e !important;
    color: #e8ede9 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: #0c1512 !important;
    border-right: 1px solid #1a2e28 !important;
}
[data-testid="stSidebar"] > div { padding-top: 2rem; }
header[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 2.5rem 2rem 6rem !important; max-width: 100% !important; }

.fw-wordmark {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #4a9e5c;
    margin-bottom: 0.2rem;
}
.fw-title {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.1;
    color: #e8ede9;
    margin-bottom: 0.4rem;
}
.fw-subtitle {
    font-size: 0.9rem;
    color: #5a7a6a;
    font-weight: 400;
    letter-spacing: 0.01em;
}
.sidebar-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a6e5c;
    margin-bottom: 0.3rem;
    margin-top: 1rem;
    display: block;
}
.sidebar-divider {
    height: 1px;
    background: #1a2e28;
    margin: 1.2rem 0;
}
.status-bar {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    padding: 0.7rem 1rem;
    background: #0c1512;
    border: 1px solid #1a2e28;
    border-radius: 6px;
}
.status-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #5a7a6a;
}
.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #4a9e5c;
    box-shadow: 0 0 6px #4a9e5c;
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: #1a2e28;
    border: 1px solid #1a2e28;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.metric-cell {
    background: #0c1512;
    padding: 1.2rem 1.4rem;
}
.metric-cell:hover { background: #0f1a16; }
.metric-eyebrow {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4a6e5c;
    margin-bottom: 0.5rem;
}
.metric-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #e8ede9;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-number.positive { color: #4a9e5c; }
.metric-number.negative { color: #ff6b4a; }
.metric-number.neutral { color: #e8ede9; }
.metric-sub { font-size: 0.72rem; color: #4a6e5c; font-weight: 400; }
.result-panel {
    background: #0c1512;
    border: 1px solid #1a2e28;
    border-radius: 8px;
    padding: 1.4rem;
    margin-bottom: 1rem;
}
.result-panel-title {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4a6e5c;
    margin-bottom: 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #1a2e28;
}
.detection-badge {
    display: inline-block;
    padding: 0.35rem 0.8rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.badge-high { background: rgba(255,107,74,0.12); color: #ff6b4a; border: 1px solid rgba(255,107,74,0.3); }
.badge-moderate { background: rgba(255,193,7,0.1); color: #e6ac00; border: 1px solid rgba(255,193,7,0.25); }
.badge-low { background: rgba(74,158,92,0.1); color: #4a9e5c; border: 1px solid rgba(74,158,92,0.25); }
.badge-none { background: rgba(74,158,92,0.1); color: #4a9e5c; border: 1px solid rgba(74,158,92,0.25); }
.ndvi-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 0;
    border-bottom: 1px solid #1a2e28;
}
.ndvi-row:last-child { border-bottom: none; }
.ndvi-label { font-size: 0.75rem; color: #5a7a6a; font-weight: 500; }
.ndvi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    font-weight: 500;
    color: #e8ede9;
}
.ndvi-date { font-size: 0.68rem; color: #3a5a4a; }
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    text-align: center;
    border: 1px dashed #1a2e28;
    border-radius: 8px;
}
.empty-state-title { font-size: 1rem; font-weight: 600; color: #3a5a4a; margin-bottom: 0.4rem; }
.empty-state-sub { font-size: 0.82rem; color: #2a3e32; }
.map-header {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4a6e5c;
    margin-bottom: 0.5rem;
}
[data-testid="stButton"] button {
    background: #1a3a28 !important;
    color: #4a9e5c !important;
    border: 1px solid #2a5a38 !important;
    border-radius: 5px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
    transition: all 0.15s !important;
}
[data-testid="stButton"] button:hover {
    background: #243e2e !important;
    border-color: #4a9e5c !important;
    color: #6ab87a !important;
}
.fw-footer {
    position: fixed;
    bottom: 0; left: 0;
    width: 100%;
    padding: 0.7rem 2rem;
    display: flex;
    align-items: center;
    gap: 2rem;
    background: #080f0e;
    border-top: 1px solid #1a2e28;
    z-index: 100;
}
.footer-item {
    font-size: 0.67rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #2a4a38;
}
.footer-item span { color: #4a9e5c; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Cached functions
# -----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def cached_analysis(lat, lon, before_start, before_end, after_start, after_end, cloud_cover):
    from core.change_detection import detect_forest_change
    return detect_forest_change(lat, lon, before_start, before_end, after_start, after_end, cloud_cover)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_timeseries(lat, lon, start, end):
    from core.timeseries import get_ndvi_timeseries
    return get_ndvi_timeseries(lat, lon, start, end)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_anomaly(lat, lon, start, end):
    from core.anomaly_detection import detect_anomalies
    return detect_anomalies(lat, lon, start, end)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("<div class='fw-wordmark'>ForestWatch AI</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:1.1rem;font-weight:700;color:#e8ede9;margin-bottom:1.5rem;'>Analysis Configuration</div>", unsafe_allow_html=True)

    st.markdown("<span class='sidebar-label'>Region</span>", unsafe_allow_html=True)
    region_name = st.selectbox("Region", list(REGIONS.keys()) + ["Custom"], label_visibility="collapsed")

    if region_name == "Custom":
        st.markdown("<span class='sidebar-label'>Latitude</span>", unsafe_allow_html=True)
        lat = st.number_input("Latitude", value=10.1632, format="%.4f", label_visibility="collapsed")
        st.markdown("<span class='sidebar-label'>Longitude</span>", unsafe_allow_html=True)
        lon = st.number_input("Longitude", value=76.6413, format="%.4f", label_visibility="collapsed")
    else:
        lat = REGIONS[region_name]["lat"]
        lon = REGIONS[region_name]["lon"]

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
    st.markdown("<span class='sidebar-label'>Before Period</span>", unsafe_allow_html=True)
    before_start = st.date_input("Before Start", value=date.today() - timedelta(days=365), label_visibility="collapsed", key="bs")
    before_end = st.date_input("Before End", value=date.today() - timedelta(days=180), label_visibility="collapsed", key="be")

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
    st.markdown("<span class='sidebar-label'>After Period</span>", unsafe_allow_html=True)
    after_start = st.date_input("After Start", value=date.today() - timedelta(days=180), label_visibility="collapsed", key="as")
    after_end = st.date_input("After End", value=date.today(), label_visibility="collapsed", key="ae")

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
    st.markdown("<span class='sidebar-label'>Max Cloud Cover</span>", unsafe_allow_html=True)
    cloud_cover = st.slider("Cloud Cover", 5, 50, 20, label_visibility="collapsed")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    analyze_clicked = st.button("Run Analysis")

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div style='margin-bottom:2rem;'>
    <div class='fw-wordmark'>ForestWatch AI — Sentinel-2 Satellite Analysis</div>
    <div class='fw-title'>Deforestation Detection</div>
    <div class='fw-subtitle'>NDVI change analysis over user-defined periods using real satellite imagery</div>
</div>
""", unsafe_allow_html=True)

if not gee_ok:
    st.error(f"Google Earth Engine connection failed: {gee_error}")
    st.stop()

st.markdown(f"""
<div class='status-bar'>
    <div class='status-item'><div class='status-dot'></div>GEE Connected</div>
    <div class='status-item'><div class='status-dot'></div>Sentinel-2 Active</div>
    <div class='status-item'><div class='status-dot'></div>Real-time Data</div>
    <div class='status-item' style='margin-left:auto; text-transform:none; letter-spacing:0;color:#3a5a4a;font-size:0.7rem;'>
        Region: {region_name} &nbsp;|&nbsp; {lat:.4f}, {lon:.4f}
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Analysis
# -----------------------------
if analyze_clicked:
    with st.spinner("Fetching satellite imagery from Google Earth Engine..."):
        try:
            result = cached_analysis(
                lat, lon,
                before_start.strftime("%Y-%m-%d"),
                before_end.strftime("%Y-%m-%d"),
                after_start.strftime("%Y-%m-%d"),
                after_end.strftime("%Y-%m-%d"),
                cloud_cover
            )
            carbon = estimate_carbon_impact(result["ndvi_change"], result["was_forested"])
            st.session_state["result"] = result
            st.session_state["carbon"] = carbon

            # Time series
            try:
                ts_df = cached_timeseries(
                    lat, lon,
                    before_start.strftime("%Y-%m-%d"),
                    after_end.strftime("%Y-%m-%d")
                )
                st.session_state["timeseries"] = ts_df
            except Exception:
                st.session_state["timeseries"] = None

            # Anomaly detection
            try:
                anomaly_result = cached_anomaly(
                    lat, lon,
                    before_start.strftime("%Y-%m-%d"),
                    after_end.strftime("%Y-%m-%d")
                )
                st.session_state["anomaly"] = anomaly_result
            except Exception:
                st.session_state["anomaly"] = None

            # Telegram alert
            from utils.alerts import check_and_alert
            alert_result = check_and_alert(region_name, result, carbon)
            st.session_state["alert_result"] = alert_result
            st.session_state["analyzed"] = True

        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.session_state["analyzed"] = False

# -----------------------------
# Results
# -----------------------------
if st.session_state.get("analyzed"):
    result = st.session_state["result"]
    carbon = st.session_state["carbon"]

    severity = result["severity"]
    ndvi_change = result["ndvi_change"]
    pct_change = result["pct_change"]

    badge_class = {
        "High": "badge-high",
        "Moderate": "badge-moderate",
        "Low": "badge-low",
        "None": "badge-none"
    }.get(severity, "badge-none")

    change_class = "negative" if ndvi_change < 0 else "positive"
    change_sign = "+" if ndvi_change >= 0 else ""

    st.markdown(f"""
    <div class='metric-grid'>
        <div class='metric-cell'>
            <div class='metric-eyebrow'>NDVI Before</div>
            <div class='metric-number neutral'>{result['before']['ndvi_mean']}</div>
            <div class='metric-sub'>{result['before']['image_date']}</div>
        </div>
        <div class='metric-cell'>
            <div class='metric-eyebrow'>NDVI After</div>
            <div class='metric-number neutral'>{result['after']['ndvi_mean']}</div>
            <div class='metric-sub'>{result['after']['image_date']}</div>
        </div>
        <div class='metric-cell'>
            <div class='metric-eyebrow'>NDVI Change</div>
            <div class='metric-number {change_class}'>{change_sign}{ndvi_change} ({change_sign}{pct_change}%)</div>
            <div class='metric-sub'>{"Loss detected" if ndvi_change < 0 else "Gain detected"}</div>
        </div>
        <div class='metric-cell'>
            <div class='metric-eyebrow'>CO2 Estimate</div>
            <div class='metric-number neutral'>{carbon['carbon_tons']:,.0f}</div>
            <div class='metric-sub'>Tons — {carbon['area_affected_ha']:,.0f} ha affected</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown("<div class='map-header'>Satellite View — Analysis Region</div>", unsafe_allow_html=True)
        m = folium.Map(location=[lat, lon], zoom_start=10, tiles=None)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Satellite"
        ).add_to(m)
        circle_color = "#ff6b4a" if result["deforested"] else "#4a9e5c"
        folium.Circle(
            [lat, lon], radius=10000,
            color=circle_color,
            weight=2,
            fill=True,
            fill_opacity=0.15,
            popup=f"NDVI: {result['after']['ndvi_mean']} | Change: {ndvi_change:+}"
        ).add_to(m)
        folium.CircleMarker(
            [lat, lon], radius=5,
            color=circle_color,
            fill=True,
            fill_opacity=1
        ).add_to(m)
        st_folium(m, height=380, use_container_width=True)

        # NDVI time series
        st.markdown("<div class='map-header' style='margin-top:1.2rem;'>NDVI Time Series</div>", unsafe_allow_html=True)
        if "timeseries" in st.session_state and st.session_state["timeseries"] is not None:
            ts_df = st.session_state["timeseries"].set_index("Date")
            st.line_chart(ts_df, color="#4a9e5c", height=200)
        else:
            chart_df = pd.DataFrame({
                "Period": ["Before", "After"],
                "NDVI": [result["before"]["ndvi_mean"], result["after"]["ndvi_mean"]]
            }).set_index("Period")
            st.bar_chart(chart_df, color="#4a9e5c", height=180)

        if st.session_state.get("anomaly"):
            anom = st.session_state["anomaly"]
            anom_color = "#ff6b4a" if anom["has_anomalies"] else "#4a9e5c"
            
            st.markdown(f"""
            <div class='map-header' style='margin-top:1.2rem;'>Anomaly Detection — Isolation Forest</div>
            <div class='result-panel' style='margin-top:0.5rem;'>
                <div class='result-panel-title'>Anomalous Months Detected</div>
                <div class='ndvi-row'>
                    <span class='ndvi-label'>Total anomalies</span>
                    <span class='ndvi-value' style='color:{anom_color};'>{anom['anomaly_count']} / {anom['total_months']} months</span>
                </div>
                <div class='ndvi-row'>
                    <span class='ndvi-label'>Most anomalous month</span>
                    <div style='text-align:right;'>
                        <div class='ndvi-value'>{anom['worst_month']}</div>
                        <div class='ndvi-date'>NDVI {anom['worst_ndvi']} — score {anom['worst_score']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            for a in anom["anomalies"]:
                st.markdown(f"""
                <div class='result-panel' style='margin-top:-0.6rem;'>
                    <div class='ndvi-row'>
                        <span class='ndvi-label'>{a['Date']}</span>
                        <div style='text-align:right;'>
                            <div class='ndvi-value' style='color:#ff6b4a;'>NDVI {a['NDVI']}</div>
                            <div class='ndvi-date'>Anomaly score: {a['anomaly_score']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div style='font-size:0.72rem;color:#3a5a4a;margin-top:0.4rem;'>
                Isolation Forest — trained on NDVI, month, rolling mean, rate of change
            </div>
            """, unsafe_allow_html=True)

    with col2:
        ml_before_label = result['ml_before']['class_label'] if result['ml_available'] else "N/A"
        ml_after_label = result['ml_after']['class_label'] if result['ml_available'] else "N/A"
        ml_before_conf = int(result['ml_before']['confidence'] * 100) if result['ml_available'] else 0
        ml_after_conf = int(result['ml_after']['confidence'] * 100) if result['ml_available'] else 0

        st.markdown(f"""
        <div class='result-panel'>
            <div class='result-panel-title'>Detection Result</div>
            <div style='margin-bottom:1rem;'>
                <span class='detection-badge {badge_class}'>{severity} Severity</span>
            </div>
            <div style='font-size:1rem;font-weight:600;color:#e8ede9;margin-bottom:0.3rem;'>{result['status']}</div>
            <div style='font-size:0.78rem;color:#4a6e5c;margin-bottom:1.2rem;'>
                {"Area was forested before analysis period." if result['was_forested'] else "Area was not classified as forested."}
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Deforestation confirmed</span>
                <span class='ndvi-value' style='color:{"#ff6b4a" if result["deforested"] else "#4a9e5c"}'>
                    {"Yes" if result["deforested"] else "No"}
                </span>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Was forested</span>
                <span class='ndvi-value'>{"Yes" if result['was_forested'] else "No"}</span>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Currently forested</span>
                <span class='ndvi-value'>{"Yes" if result['is_forested'] else "No"}</span>
            </div>
        </div>
        <div class='result-panel'>
            <div class='result-panel-title'>AI Land Cover Classification</div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Before period</span>
                <div style='text-align:right;'>
                    <div class='ndvi-value'>{ml_before_label}</div>
                    <div class='ndvi-date'>Confidence: {ml_before_conf}%</div>
                </div>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>After period</span>
                <div style='text-align:right;'>
                    <div class='ndvi-value'>{ml_after_label}</div>
                    <div class='ndvi-date'>Confidence: {ml_after_conf}%</div>
                </div>
            </div>
            <div style='font-size:0.72rem;color:#3a5a4a;margin-top:0.8rem;'>
                Random Forest classifier — 8 Sentinel-2 features
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='result-panel'>
            <div class='result-panel-title'>NDVI Detail</div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Before mean</span>
                <div style='text-align:right;'>
                    <div class='ndvi-value'>{result['before']['ndvi_mean']}</div>
                    <div class='ndvi-date'>{result['before']['image_date']} &nbsp;|&nbsp; {result['before']['images_available']} images</div>
                </div>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>After mean</span>
                <div style='text-align:right;'>
                    <div class='ndvi-value'>{result['after']['ndvi_mean']}</div>
                    <div class='ndvi-date'>{result['after']['image_date']} &nbsp;|&nbsp; {result['after']['images_available']} images</div>
                </div>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Before min / max</span>
                <span class='ndvi-value' style='font-size:0.78rem;'>{result['before']['ndvi_min']} / {result['before']['ndvi_max']}</span>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>After min / max</span>
                <span class='ndvi-value' style='font-size:0.78rem;'>{result['after']['ndvi_min']} / {result['after']['ndvi_max']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='result-panel'>
            <div class='result-panel-title'>Carbon Impact Estimate</div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Area affected</span>
                <span class='ndvi-value'>{carbon['area_affected_ha']:,.0f} ha</span>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>CO2 estimate</span>
                <span class='ndvi-value'>{carbon['carbon_tons']:,.0f} tons</span>
            </div>
            <div class='ndvi-row'>
                <span class='ndvi-label'>Carbon credits</span>
                <span class='ndvi-value'>{carbon['carbon_credits']:,}</span>
            </div>
            <div style='font-size:0.72rem;color:#3a5a4a;margin-top:0.8rem;'>{carbon['note']}</div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-state-title'>No analysis loaded</div>
        <div class='empty-state-sub'>Select a region and date range in the sidebar, then click Run Analysis.</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<div class='fw-footer'>
    <div class='footer-item'><span>GEE</span> Connected</div>
    <div class='footer-item'><span>Sentinel-2</span> SR Harmonized</div>
    <div class='footer-item'><span>Resolution</span> 10m</div>
    <div class='footer-item' style='margin-left:auto;'>ForestWatch AI</div>
</div>
""", unsafe_allow_html=True)

