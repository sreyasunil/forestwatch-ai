import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from core.gee_auth import initialize_gee
from core.timeseries import get_ndvi_timeseries

initialize_gee()

def build_features(df: pd.DataFrame) -> np.ndarray:
    """
    Build feature matrix from NDVI time series for anomaly detection.
    
    WHY multiple features instead of just NDVI:
    Isolation Forest works better with more context.
    Month number captures seasonality — the model learns that
    February NDVI = 0.65 is normal but July NDVI = 0.65 is suspicious
    because July should be higher (monsoon season).
    
    Features:
    - NDVI value
    - Month number (1-12) — captures seasonal cycle
    - NDVI rolling mean (3 month) — smoothed trend
    - NDVI difference from previous month — rate of change
    """
    df = df.copy().sort_values("Date").reset_index(drop=True)

    df["month"] = df["Date"].dt.month
    df["ndvi_rolling"] = df["NDVI"].rolling(window=3, min_periods=1).mean()
    df["ndvi_diff"] = df["NDVI"].diff().fillna(0)

    features = df[["NDVI", "month", "ndvi_rolling", "ndvi_diff"]].values
    return features, df


def detect_anomalies(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    cloud_cover: int = 20,
    contamination: float = 0.1
) -> dict:
    """
    Detect anomalous NDVI drops in a time series using Isolation Forest.
    
    WHY contamination=0.1:
    Tells the model to expect ~10% of data points to be anomalies.
    For a 24-month series that's ~2-3 anomalous months — reasonable
    for a region with occasional deforestation or drought events.
    
    Returns anomaly scores and flags for each month in the series.
    """
    # Get time series data
    df = get_ndvi_timeseries(lat, lon, start_date, end_date, cloud_cover)

    if len(df) < 6:
        raise ValueError(
            "Not enough data points for anomaly detection. "
            "Use a date range of at least 12 months."
        )

    features, df = build_features(df)

    # Train Isolation Forest
    # WHY n_estimators=100: 100 trees gives stable anomaly scores
    # WHY random_state=42: reproducible results
    clf = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42
    )
    clf.fit(features)

    # Predict: -1 = anomaly, 1 = normal
    predictions = clf.predict(features)
    # Anomaly score: more negative = more anomalous
    scores = clf.decision_function(features)
    # Normalize scores to 0-1 range for display
    normalized_scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)

    df["anomaly"] = predictions == -1
    df["anomaly_score"] = (1 - normalized_scores).round(4)  # higher = more anomalous

    # Extract anomalous months
    anomalies = df[df["anomaly"] == True][["Date", "NDVI", "anomaly_score"]].copy()
    anomalies["Date"] = anomalies["Date"].dt.strftime("%Y-%m")

    # Find most anomalous point
    worst_idx = df["anomaly_score"].idxmax()
    worst = df.loc[worst_idx]

    return {
        "timeseries": df,
        "anomalies": anomalies.to_dict("records"),
        "anomaly_count": int(df["anomaly"].sum()),
        "total_months": len(df),
        "worst_month": worst["Date"].strftime("%Y-%m"),
        "worst_ndvi": round(float(worst["NDVI"]), 4),
        "worst_score": round(float(worst["anomaly_score"]), 4),
        "has_anomalies": len(anomalies) > 0
    }