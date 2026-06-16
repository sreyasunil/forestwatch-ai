import ee
# from core.gee_auth import initialize_gee

# initialize_gee()

def get_sentinel2_ndvi(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    cloud_cover: int = 20
) -> dict:
    """
    Fetch Sentinel-2 imagery and compute NDVI + band values.
    Returns NDVI stats, image metadata, and raw band values for ML classifier.
    """
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)

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
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

    # EVI = Enhanced Vegetation Index
    # WHY: More accurate than NDVI in dense canopy areas like Amazon
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {
            'NIR': image.select('B8'),
            'RED': image.select('B4'),
            'BLUE': image.select('B2')
        }
    ).rename("EVI")

    full_image = image.select(["B2","B3","B4","B8","B11","B12"]).addBands(ndvi).addBands(evi)

    # WHY combine reducers: get mean of all bands in one GEE call
    # instead of 8 separate calls — much faster
    stats = full_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    # NDVI min/max separately for display
    ndvi_stats = ndvi.reduceRegion(
        reducer=ee.Reducer.min().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=region,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    date_acquired = image.date().format("YYYY-MM-dd").getInfo()

    return {
        "ndvi_mean": round(stats.get("NDVI", 0) or 0, 4),
        "ndvi_min": round(ndvi_stats.get("NDVI_min", 0) or 0, 4),
        "ndvi_max": round(ndvi_stats.get("NDVI_max", 0) or 0, 4),
        "image_date": date_acquired,
        "images_available": count,
        "region": {"lat": lat, "lon": lon, "radius_km": 10},
        # Band values for ML classifier
        "bands": {
            "B2":   round(stats.get("B2", 0) or 0, 2),
            "B3":   round(stats.get("B3", 0) or 0, 2),
            "B4":   round(stats.get("B4", 0) or 0, 2),
            "B8":   round(stats.get("B8", 0) or 0, 2),
            "B11":  round(stats.get("B11", 0) or 0, 2),
            "B12":  round(stats.get("B12", 0) or 0, 2),
            "NDVI": round(stats.get("NDVI", 0) or 0, 4),
            "EVI":  round(stats.get("EVI", 0) or 0, 4),
        }
    }