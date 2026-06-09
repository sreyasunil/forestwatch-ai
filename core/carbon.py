# Carbon estimation based on forest area and NDVI change
# Source: IPCC estimates ~150-200 tons CO2 per hectare for tropical forests

CARBON_PER_HECTARE = 175  # tons CO2 (tropical forest average)
AREA_PER_UNIT = 31416     # hectares in a 10km radius circle (pi * 10^2 * 100)

def estimate_carbon_impact(ndvi_change: float, was_forested: bool) -> dict:
    """
    Estimate carbon impact from NDVI change.
    Negative NDVI change in forested area = carbon release.
    Positive NDVI change = carbon sequestration.
    """
    if not was_forested and ndvi_change < 0:
        return {
            "carbon_tons": 0,
            "carbon_credits": 0,
            "area_affected_ha": 0,
            "note": "Area was not forested. No carbon impact calculated."
        }

    # Estimate proportion of area affected by change
    change_intensity = min(abs(ndvi_change) / 0.5, 1.0)
    area_affected = round(AREA_PER_UNIT * change_intensity, 1)
    carbon_tons = round(area_affected * CARBON_PER_HECTARE, 1)
    carbon_credits = round(carbon_tons)  # 1 credit = 1 ton CO2

    if ndvi_change < 0:
        note = "Carbon released due to vegetation loss."
    else:
        note = "Carbon sequestered due to vegetation gain."

    return {
        "carbon_tons": carbon_tons,
        "carbon_credits": carbon_credits,
        "area_affected_ha": area_affected,
        "note": note
    }