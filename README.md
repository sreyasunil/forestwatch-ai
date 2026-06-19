# ForestWatch AI

> Real-time deforestation detection and climate impact analysis using Sentinel-2 satellite imagery and Google Earth Engine.
**Live demo:** https://fwatch-ai.streamlit.app

Built by [Sreya Sunil](https://github.com/sreyasunil)

---

## Purpose

Deforestation is one of the leading contributors to climate change, biodiversity loss, and increased carbon emissions. Traditional monitoring methods rely on manual field surveys and periodic reports — too slow to catch illegal logging or rapid land clearing before significant damage is done.

ForestWatch AI automates this process. It pulls real Sentinel-2 satellite imagery from Google Earth Engine, computes vegetation indices, classifies land cover using a trained machine learning model, and alerts environmental agencies or researchers the moment significant forest loss is detected.

The goal is early detection. A system that tells you forest was lost three months ago is useful for reporting. A system that tells you forest is being lost right now is useful for intervention.

---

## Key Features

- **Real satellite data** — Sentinel-2 SR Harmonized imagery at 10m resolution. No mock data, no simulations. Every analysis fetches live measurements from Google Earth Engine.
- **NDVI change detection** — computes Normalized Difference Vegetation Index for two user-defined time periods and quantifies vegetation loss or gain.
- **Random Forest land cover classifier** — trained on real Sentinel-2 spectral band values (B2, B3, B4, B8, B11, B12, NDVI, EVI) to classify areas as Dense Forest, Degraded Forest, Deforested, Agriculture, or Urban with confidence scores.
- **NDVI time series** — pulls monthly NDVI over the full analysis period to reveal seasonal patterns, gradual degradation, and the exact timing of vegetation change.
- **Carbon impact estimation** — estimates CO2 released based on affected area and IPCC tropical forest carbon density values (175 tons CO2/ha).
- **Telegram alerts** — sends formatted real-time notifications to a configured Telegram bot when NDVI drop exceeds the detection threshold.
- **Result caching** — repeated queries on the same region and dates return instantly without re-fetching satellite data.
- **PDF report export** — generates downloadable compliance-style reports for agency or research use.

---

## Intended Users

ForestWatch AI is designed for:

* Government forest and environmental agencies
* Conservation and environmental NGOs
* Climate and biodiversity researchers
* Land-use monitoring organizations
* ESG and sustainability teams

The platform supports satellite-based forest monitoring, deforestation detection, and environmental impact assessment to enable faster, data-driven decision making.

---

## Technology Stack

| Component | Technology |
|---|---|
| Dashboard UI | Streamlit |
| Satellite data | Google Earth Engine API |
| Imagery source | Sentinel-2 SR Harmonized (ESA Copernicus) |
| ML classifier | scikit-learn Random Forest |
| Map visualization | Folium + streamlit-folium |
| Alert system | Telegram Bot API |
| Data processing | pandas, numpy |
| PDF export | ReportLab |
| Environment config | python-dotenv |
| Language | Python 3.13 |

---

## Project Structure

```
forestwatch-ai/
├── app.py                  # Streamlit dashboard and UI orchestration
├── core/
│   ├── gee_auth.py         # Google Earth Engine authentication
│   ├── satellite.py        # Sentinel-2 fetch, NDVI and band computation
│   ├── change_detection.py # Before/after comparison and severity classification
│   ├── carbon.py           # Carbon impact estimation
│   ├── timeseries.py       # Monthly NDVI time series generation
│   └── ml_classifier.py    # Random Forest training and land cover inference
├── config/
│   └── regions.py          # Preset region coordinates
├── utils/
│   ├── alerts.py           # Telegram alert system
│   └── export.py           # PDF report generation
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── LICENSE                 # MIT License
```

---

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- An approved [Google Earth Engine](https://earthengine.google.com/) account
- A Telegram bot token (optional — required only for alerts)

### Step 1 — Clone the repository

```bash
git clone https://github.com/sreyasunil/forestwatch-ai.git
cd forestwatch-ai
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Authenticate Google Earth Engine

Run this once. It opens a browser for Google login and saves credentials locally on your machine.

```bash
python -c "import ee; ee.Authenticate()"
```

Then verify the connection works:

```bash
python -c "import ee; ee.Initialize(project='your-gee-project-id'); print('GEE Connected')"
```

### Step 4 — Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and add your Telegram credentials:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

To get these:
- Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
- Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

### Step 5 — Run the app

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`

---

## Usage Instructions

1. **Select a region** from the sidebar — Amazon, Kerala, Borneo, Congo, or enter custom coordinates
2. **Set the Before period** — the baseline date range (e.g. 2022/01/01 to 2022/12/31)
3. **Set the After period** — the comparison date range (e.g. 2023/01/01 to 2023/12/31)
4. **Adjust cloud cover** threshold if needed (default 20%)
5. **Click Run Analysis** — the app fetches real satellite data, runs the ML classifier, and generates results
6. **Review results** — NDVI metrics, land cover classification, time series chart, carbon impact estimate
7. **Check Telegram** — if vegetation loss exceeds the alert threshold, a formatted message is sent automatically

**Recommended date ranges:** Use full year ranges (Jan to Dec) for best results. Avoid ranges shorter than 3 months — fewer clear images increase the chance of cloud contamination.

**Sentinel-2 data availability:** Reliable from 2017 onwards. Pre-2017 queries will return limited or no results.

---

## Supported Regions

| Region | Coordinates | Notes |
|---|---|---|
| Amazon Rainforest | -3.4653, -62.2159 | Primary deforestation hotspot |
| Western Ghats, Kerala | 10.1632, 76.6413 | Biodiversity hotspot, India |
| Borneo Rainforest | 0.9619, 114.5548 | High deforestation rate |
| Congo Basin | -0.7893, 23.6560 | World's second largest rainforest |
| Custom | User defined | Any coordinates worldwide |

---

## How NDVI Works

NDVI (Normalized Difference Vegetation Index) measures vegetation health from satellite data:

```
NDVI = (NIR - Red) / (NIR + Red)
```

- **NIR (Band 8)** — healthy vegetation reflects near-infrared strongly
- **Red (Band 4)** — chlorophyll absorbs red light for photosynthesis

| NDVI Range | Interpretation |
|---|---|
| 0.6 – 0.9 | Dense healthy forest |
| 0.4 – 0.6 | Degraded or sparse forest |
| 0.2 – 0.4 | Shrubland or regrowth |
| 0.0 – 0.2 | Bare soil or cleared land |
| < 0.0 | Water or built surfaces |

---

## Future Improvements

- **Forest polygon extraction** — export actual deforested area boundaries as GeoJSON from GEE instead of fixed radius circles, enabling precise area measurement
- **Anomaly detection** — Isolation Forest model trained on multi-year NDVI time series to distinguish seasonal variation from actual deforestation events
- **Deforestation risk prediction** — gradient boosting model using historical NDVI trends and spatial features to predict which areas are at risk in the next 3-6 months
- **SAR data fusion** — combine Sentinel-1 radar imagery with Sentinel-2 optical data for cloud-independent detection
- **Global alert monitoring** — scheduled daily analysis across multiple regions with automated Telegram reporting
- **Mobile application** — React Native app for field researchers
- **Ground truth integration** — incorporate human-verified land cover labels to improve ML classifier accuracy beyond weakly supervised training

---

## Honest Limitations

- Carbon estimation uses IPCC average values (175 tons CO2/ha) — not location-specific biomass measurements
- ML classifier uses weakly supervised labels generated from NDVI thresholds, not human-verified ground truth
- Analysis covers a 10km radius circle — not administrative or watershed boundaries
- Single point analysis — does not yet produce spatial deforestation maps
- Sentinel-2 data available from 2017 onwards only

---

## Author

**Sreya Sunil** — [github.com/sreyasunil](https://github.com/sreyasunil)

## License

MIT — see [LICENSE](LICENSE) for details.
