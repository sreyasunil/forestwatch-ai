from core.satellite import get_sentinel2_ndvi

NDVI_FOREST_THRESHOLD = 0.4  # Below this = not forest

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
    Compare NDVI between two time periods to detect forest loss.
    Returns change metrics and classification.
    """
    before = get_sentinel2_ndvi(lat, lon, before_start, before_end, cloud_cover)
    after = get_sentinel2_ndvi(lat, lon, after_start, after_end, cloud_cover)

    ndvi_change = round(after["ndvi_mean"] - before["ndvi_mean"], 4)
    pct_change = round((ndvi_change / before["ndvi_mean"]) * 100, 2) if before["ndvi_mean"] != 0 else 0

    # Classify change
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

    # Was it forested before?
    was_forested = before["ndvi_mean"] >= NDVI_FOREST_THRESHOLD
    is_forested = after["ndvi_mean"] >= NDVI_FOREST_THRESHOLD
    deforested = was_forested and not is_forested

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
    }