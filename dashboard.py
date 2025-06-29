import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os
import requests

# --- Config ---
st.set_page_config(layout="wide")
st.title("🛸 Drone Incursion Detection Dashboard")

log_file = "data/flight_logs.csv"
columns = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "heading", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source", "category", "timestamp"
]

# --- Fetch and Save Live Data ---
if st.button("🔄 Refresh"):
    url = "https://opensky-network.org/api/states/all"
    params = {"extended": 1}
    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")
    try:
        response = requests.get(url, auth=(username, password), params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("states"):
            df_live = pd.DataFrame(data["states"], columns=columns[:-1])
            df_live["timestamp"] = datetime.utcfromtimestamp(data["time"]).strftime('%Y-%m-%d %H:%M:%S')
            df_live = df_live[columns]  # Ensure correct column order
            os.makedirs("data", exist_ok=True)
            df_live.to_csv(log_file, index=False)  # ✅ This includes headers by default
        else:
            st.warning("No state data received.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

# --- Load and Validate CSV ---
try:
    df = pd.read_csv(log_file)
    required_cols = ["callsign", "velocity", "baro_altitude", "latitude", "longitude", "category"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing columns in CSV: {missing_cols}")
except Exception as e:
    st.error(f"Failed to load or parse flight log data: {e}")
    st.stop()


# --- Data Cleaning ---
df["callsign"] = df["callsign"].fillna("").astype(str)
df["velocity"] = pd.to_numeric(df["velocity"], errors='coerce')
df["baro_altitude"] = pd.to_numeric(df["baro_altitude"], errors='coerce')

# --- Anomaly Detection ---
anomalies = df[
    ((df["baro_altitude"] < 1000) & (df["velocity"] < 50)) |
    (df["callsign"].str.strip() == "") |
    (df["category"] == 8)
].copy()

anomalies.to_csv("data/anomalies_only.csv", index=False)

# --- Sidebar Filters ---
st.sidebar.header("Filter Anomalies")
selected_countries = st.sidebar.multiselect(
    "Origin Country", options=sorted(anomalies["origin_country"].dropna().unique()))
alt_range = st.sidebar.slider("Altitude Range (feet)", 0, 5000, (0, 1500))
selected_categories = st.sidebar.multiselect(
    "Aircraft Category", options=sorted(anomalies["category"].dropna().unique()))

lat_range = st.sidebar.slider("Latitude Range", -90.0, 90.0, (24.0, 49.0))
lon_range = st.sidebar.slider("Longitude Range", -180.0, 180.0, (-125.0, -66.9))

filtered = anomalies.copy()
if selected_countries:
    filtered = filtered[filtered["origin_country"].isin(selected_countries)]
if selected_categories:
    filtered = filtered[filtered["category"].isin(selected_categories)]
filtered = filtered[
    (filtered["baro_altitude"] >= alt_range[0]) &
    (filtered["baro_altitude"] <= alt_range[1]) &
    (filtered["latitude"] >= lat_range[0]) &
    (filtered["latitude"] <= lat_range[1]) &
    (filtered["longitude"] >= lon_range[0]) &
    (filtered["longitude"] <= lon_range[1])
]

# --- Results Table ---
st.subheader("⚠️ Filtered Anomalous Aircraft")
st.dataframe(filtered[[
    "icao24", "origin_country", "latitude", "longitude",
    "baro_altitude", "velocity", "category", "timestamp"
]])

# --- Legend ---
category_map = {
    0: "No info", 1: "Light (< 15,500 lbs)", 2: "Small (15,500–75,000 lbs)",
    3: "Medium (75,000–300,000 lbs)", 4: "Heavy (> 300,000 lbs)", 5: "High vortex",
    6: "Glider", 7: "Helicopter", 8: "UAV (likely drone)", 9: "Spacecraft",
    10: "Surface emergency", 11: "Surface service", 12: "Fixed ground", 13: "Unknown"
}
present = set(filtered["category"].dropna().unique())
legend = {k: v for k, v in category_map.items() if k in present}
st.markdown("### 📘 Category Legend")
st.json(legend)

# --- Anomaly Map ---
st.subheader("📍 Anomaly Map")
if not filtered.empty:
    map_center = [filtered["latitude"].mean(), filtered["longitude"].mean()]
else:
    map_center = [38.0, -122.0]

m = folium.Map(location=map_center, zoom_start=5)
for _, row in filtered.iterrows():
    if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=6,
            color='red',
            fill=True,
            fill_opacity=0.8,
            popup=f"""<b>⚠️ <a href="https://globe.adsbexchange.com/?icao={row['icao24']}" target="_blank">{row['icao24']}</a></b><br>{row['origin_country']}"""
        ).add_to(m)

st_folium(m, width=1000, height=550)
