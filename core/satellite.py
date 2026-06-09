import ee
from datetime import date
from core.gee_auth import initialize_gee

initialize_gee()

def get_sentinel2_ndvi(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    cloud_cover: int = 20
) -> dict:
    """
    Fetch Sentinel-2 imagery and compute NDVI for a given location and date range.
    Returns a dict with NDVI mean, min, max and image metadata.
    """
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)  # 10km radius around point

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_cover))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )

    count = collection.size().getInfo()
    if count == 0:
        raise ValueError(
            f"No Sentinel-2 images found for this location and date range. "
            f"Try a wider date range or higher cloud cover threshold."
        )

    image = collection.first()

    # NDVI = (NIR - Red) / (NIR + Red)
    # Sentinel-2 bands: B8 = NIR, B4 = Red
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

    stats = ndvi.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.max(), sharedInputs=True),
        geometry=region,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    date_acquired = image.date().format("YYYY-MM-dd").getInfo()

    return {
        "ndvi_mean": round(stats.get("NDVI_mean", 0), 4),
        "ndvi_min": round(stats.get("NDVI_min", 0), 4),
        "ndvi_max": round(stats.get("NDVI_max", 0), 4),
        "image_date": date_acquired,
        "images_available": count,
        "region": {"lat": lat, "lon": lon, "radius_km": 10}
    }