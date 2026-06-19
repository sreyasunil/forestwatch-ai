from core.satellite import get_sentinel2_ndvi
from core.ml_classifier import predict_land_cover, load_model
import os

NDVI_FOREST_THRESHOLD = 0.4

def detect_forest_change(
    lat: float,
    lon: float,
    before_start: str,
    before_end: str,
    after_start: str,
    after_end: str,
    cloud_cover: int = 20
) -> dict:
    """
    Compare NDVI and ML land cover classification between two time periods.
    
    WHY two approaches combined:
    - NDVI change = simple, fast, interpretable
    - ML classifier = uses all 8 features, learned from real data
    Both together give more confidence than either alone.
    """
    before = get_sentinel2_ndvi(lat, lon, before_start, before_end, cloud_cover)
    after = get_sentinel2_ndvi(lat, lon, after_start, after_end, cloud_cover)

    ndvi_change = round(after["ndvi_mean"] - before["ndvi_mean"], 4)
    pct_change = round((ndvi_change / before["ndvi_mean"]) * 100, 2) if before["ndvi_mean"] != 0 else 0

    # Rule-based classification (kept as fallback)
    if ndvi_change < -0.15:
        status = "Significant Loss"
        severity = "High"
    elif ndvi_change < -0.05:
        status = "Moderate Loss"
        severity = "Moderate"
    elif ndvi_change < 0:
        status = "Minor Loss"
        severity = "Low"
    elif ndvi_change > 0.05:
        status = "Vegetation Gain"
        severity = "None"
    else:
        status = "No Significant Change"
        severity = "None"

    was_forested = before["ndvi_mean"] >= NDVI_FOREST_THRESHOLD
    is_forested = after["ndvi_mean"] >= NDVI_FOREST_THRESHOLD
    deforested = was_forested and not is_forested

    # ML classification
    # WHY: uses all 8 band features, not just NDVI
    # gives confidence score and land cover label
    ml_before = None
    ml_after = None
    ml_available = False

    try:
        if not os.path.exists("core/rf_model.joblib"):
            from core.ml_classifier import train_model
            train_model(lat, lon)
        ml_before = predict_land_cover(before["bands"])
        ml_after = predict_land_cover(after["bands"])
        ml_available = True
    except Exception as e:
        ml_available = False

    return {
        "before": before,
        "after": after,
        "ndvi_change": ndvi_change,
        "pct_change": pct_change,
        "status": status,
        "severity": severity,
        "was_forested": was_forested,
        "is_forested": is_forested,
        "deforested": deforested,
        # ML results
        "ml_available": ml_available,
        "ml_before": ml_before,
        "ml_after": ml_after,
    }