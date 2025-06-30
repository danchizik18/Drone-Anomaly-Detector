import pandas as pd
import requests
from datetime import datetime
from shapely.geometry import Point, Polygon
import streamlit as st
import folium
from streamlit_folium import st_folium
import joblib
import os

st.set_page_config(layout="wide")
st.title("🛡️ Airspace Intrusion Detection Dashboard")

# Define more realistic restricted zones (e.g. military bases or sensitive facilities)
RESTRICTED_ZONES = [
    Polygon([(-77.055, 38.85), (-77.035, 38.85), (-77.035, 38.87), (-77.055, 38.87)]),  # Pentagon area
    Polygon([(-122.39, 37.61), (-122.36, 37.61), (-122.36, 37.63), (-122.39, 37.63)]),  # Near SF Airport
    Polygon([(-106.49, 35.03), (-106.47, 35.03), (-106.47, 35.05), (-106.49, 35.05)])   # Kirtland AFB
]

def fetch_opensky_data():
    url = "https://opensky-network.org/api/states/all?extended=0"
    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("states"):
        df = pd.DataFrame(data["states"])
        if df.shape[1] == 17:
            df.columns = [
                "icao24", "callsign", "origin_country", "time_position", "last_contact",
                "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
                "heading", "vertical_rate", "squawk", "spi", "position_source",
                "category", "other"
            ]
        else:
            st.warning(f"[WARN] Unexpected number of columns: {df.shape[1]}")
            return pd.DataFrame()

        df = df.dropna(subset=["latitude", "longitude", "heading"])
        df["timestamp"] = datetime.utcfromtimestamp(data["time"])
        return df

    return pd.DataFrame()

def detect_intrusions(df):
    intrusions = []
    for _, row in df.iterrows():
        point = Point(row["longitude"], row["latitude"])
        for zone in RESTRICTED_ZONES:
            if zone.contains(point):
                intrusions.append(row)
                break

    if intrusions:
        intrusions_df = pd.DataFrame(intrusions)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = f"logs/intrusions_{timestamp}.csv"
        os.makedirs("logs", exist_ok=True)
        intrusions_df.to_csv(path, index=False)
        return intrusions_df
    return pd.DataFrame()

def classify_intrusion_risk(df, model_path="ml_model.pkl"):
    if not os.path.exists(model_path):
        st.warning("ML model not found. Skipping risk classification.")
        df["risk_level"] = "unknown"
        return df
    try:
        model = joblib.load(model_path)
        features = df[["velocity", "heading"]].fillna(0)
        df["risk_level"] = model.predict(features)
        return df
    except Exception as e:
        st.warning(f"Risk classification skipped due to model error: {e}")
        df["risk_level"] = "unknown"
        return df

st.sidebar.markdown("### Controls")
if st.sidebar.button("🔄 Refresh Data"):
    st.session_state["df"] = fetch_opensky_data()
    st.session_state["intrusions"] = detect_intrusions(st.session_state["df"])
    if not st.session_state["intrusions"].empty:
        st.session_state["intrusions"] = classify_intrusion_risk(st.session_state["intrusions"])

if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame()
    st.session_state["intrusions"] = pd.DataFrame()

if not st.session_state["df"].empty:
    st.write(f"[INFO] Retrieved {len(st.session_state['df'])} aircraft.")

if not st.session_state["intrusions"].empty:
    st.success(f"[ALERT] Detected {len(st.session_state['intrusions'])} intrusions.")
    intrusions = st.session_state["intrusions"]

    st.dataframe(intrusions[[
        "icao24", "callsign", "origin_country", "latitude", "longitude",
        "velocity", "heading", "risk_level", "timestamp"
    ]])

    st.subheader("📍 Map View of Intrusions")
    m = folium.Map(location=[39.5, -98.35], zoom_start=4)
    for zone in RESTRICTED_ZONES:
        folium.Polygon(locations=[(lat, lon) for lon, lat in zone.exterior.coords],
                       color='red', fill=True, fill_opacity=0.1,
                       tooltip="Restricted Zone").add_to(m)

    for _, row in intrusions.iterrows():
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    popup=f"{row['callsign']} ({row['risk_level']})",
                    color="crimson",
                    fill=True,
                    fill_opacity=0.7
                ).add_to(m)
        except Exception:
            continue

    st_folium(m, width=1000, height=550)
else:
    st.info("No intrusions detected.")
