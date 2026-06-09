import ee

def initialize_gee(project: str = "nexora-491517"):
    """
    Initialize Google Earth Engine.
    Credentials are stored locally after ee.Authenticate() is run once.
    Never store JSON keys in the repo.
    """
    try:
        ee.Initialize(project=project)
        return True
    except Exception as e:
        raise RuntimeError(f"GEE initialization failed: {e}")