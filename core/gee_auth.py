import ee
import json
import os

def initialize_gee(project: str = "nexora-491517"):
    """
    Initialize GEE with two auth modes:
    
    Local development:
    Uses credentials saved by ee.Authenticate() on your machine.
    
    Deployed (Streamlit Cloud):
    Uses service account JSON stored in st.secrets.
    Never stored in code or repo.
    """
    # Check if running on Streamlit Cloud with secrets configured
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'GEE_SERVICE_ACCOUNT' in st.secrets:
            service_account_info = json.loads(st.secrets["GEE_SERVICE_ACCOUNT"])
            credentials = ee.ServiceAccountCredentials(
                email=service_account_info["client_email"],
                key_data=json.dumps(service_account_info)
            )
            ee.Initialize(credentials=credentials, project=project)
            return True
    except Exception:
        pass

    # Fall back to local credentials
    try:
        ee.Initialize(project=project)
        return True
    except Exception as e:
        raise RuntimeError(f"GEE initialization failed: {e}")