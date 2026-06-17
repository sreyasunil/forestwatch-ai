# import ee
# import json
# import os

# def initialize_gee(project: str = "nexora-491517"):
#     """
#     Initialize GEE with two auth modes:
#     Local: uses credentials saved by ee.Authenticate()
#     Deployed: uses service account JSON from Streamlit secrets
#     """
#     # Try Streamlit secrets first
#     try:
#         import streamlit as st
#         if "GEE_SERVICE_ACCOUNT" in st.secrets:
#             service_account_info = json.loads(st.secrets["GEE_SERVICE_ACCOUNT"])
#             credentials = ee.ServiceAccountCredentials(
#                 email=service_account_info["client_email"],
#                 key_data=json.dumps(service_account_info)
#             )
#             ee.Initialize(credentials=credentials, project=project)
#             return True
#     except Exception as e:
#         pass

#     # Fall back to local credentials
#     try:
#         ee.Initialize(project=project)
#         return True
#     except Exception as e:
#         raise RuntimeError(f"GEE initialization failed: {e}")


import ee
import json
import os

def initialize_gee(project: str = "nexora-491517"):
    try:
        import streamlit as st
        if "GEE_SERVICE_ACCOUNT" in st.secrets:
            service_account_info = json.loads(st.secrets["GEE_SERVICE_ACCOUNT"])
            credentials = ee.ServiceAccountCredentials(
                email=service_account_info["client_email"],
                key_data=json.dumps(service_account_info)
            )
            ee.Initialize(credentials=credentials, project=project)
            return True
        else:
            raise RuntimeError("GEE_SERVICE_ACCOUNT not found in secrets")
    except Exception as e:
        # Fall back to local credentials
        try:
            ee.Initialize(project=project)
            return True
        except Exception as e2:
            secret_exists = "GEE_SERVICE_ACCOUNT" in st.secrets if hasattr(st, 'secrets') else False
            raise RuntimeError(f"GEE failed. Secret exists: {secret_exists}. Error: {e2}")