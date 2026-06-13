import ee
import pandas as pd
from core.gee_auth import initialize_gee

initialize_gee()

def get_ndvi_timeseries(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    cloud_cover: int = 20
) -> pd.DataFrame:
    """
    Get monthly NDVI values for a location over a date range.
    
    WHY monthly composites:
    Single images have clouds, shadows, sensor noise.
    Monthly median composite averages out these artifacts
    giving a cleaner NDVI signal that reflects actual
    vegetation change, not cloud shadows.
    """
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(10000)

    # WHY: We create monthly composites by mapping over
    # a sequence of months and taking median NDVI each month
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_cover))
    )

    def monthly_ndvi(image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        mean_ndvi = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=100,
            maxPixels=1e9
        )
        return image.set("ndvi_mean", mean_ndvi.get("NDVI")) \
                    .set("month_date", image.date().format("YYYY-MM"))

    with_ndvi = collection.map(monthly_ndvi)

    # Get list of results
    results = with_ndvi.reduceColumns(
        ee.Reducer.toList(2),
        ["month_date", "ndvi_mean"]
    ).getInfo()

    data = results.get("list", [])

    if not data:
        raise ValueError("No data returned for this location and date range.")

    rows = []
    for item in data:
        try:
            date_str, ndvi_val = item
            if ndvi_val is not None:
                rows.append({
                    "Date": pd.to_datetime(date_str),
                    "NDVI": round(float(ndvi_val), 4)
                })
        except:
            continue

    if not rows:
        raise ValueError("Could not parse time series data.")

    df = pd.DataFrame(rows)
    # WHY groupby: multiple images per month → take mean per month
    df = df.groupby(df["Date"].dt.to_period("M")).agg({"NDVI": "mean"}).reset_index()
    df["Date"] = df["Date"].dt.to_timestamp()
    df["NDVI"] = df["NDVI"].round(4)
    df = df.sort_values("Date")

    return df