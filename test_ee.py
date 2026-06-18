import ee
import json

with open(r"C:\Users\user\Downloads\nexora-491517-44fd90a3e958.json") as f:
    info = json.load(f)

credentials = ee.ServiceAccountCredentials(
    email=info["client_email"],
    key_file=r"C:\Users\user\Downloads\nexora-491517-44fd90a3e958.json"
)

ee.Initialize(credentials=credentials, project="nexora-491517")

print("SUCCESS")