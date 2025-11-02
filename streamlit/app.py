import streamlit as st
import ee

st.title("🌍 GEE Authentication Test")

SERVICE_ACCOUNT = "your-service-account@your-project.iam.gserviceaccount.com"
KEY_PATH = "../service-account-key.json"  # adjust path if needed

try:
    credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY_PATH)
    ee.Initialize(credentials)
    st.success("✅ Earth Engine initialized successfully!")
except Exception as e:
    st.error(f"❌ Failed to initialize Earth Engine: {e}")
