import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os

st.set_page_config(layout="wide")
st.title("🛸 Drone Incursion Detection Dashboard")

if st.button("🔄 Refresh"):
    st.rerun()

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

log_file = "data/flight_logs.csv"

columns = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "heading", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source", "category", "timestamp"
]

if os.path.exists(log_file):
    df = pd.read_csv(log_file, names=columns)
else:
    st.error("No flight log data found.")
    st.stop()

df["callsign"] = df["callsign"].fillna("").astype(str)
df["velocity"] = pd.to_numeric(df["velocity"], errors='coerce')
df["baro_altitude"] = pd.to_numeric(df["baro_altitude"], errors='coerce')

anomalies = df[
    ((df["baro_altitude"] < 1000) & (df["velocity"] < 50)) |
    (df["callsign"].str.strip() == "") |
    (df["category"] == 8)
].copy()

anomalies.to_csv("data/anomalies_only.csv", index=False)

st.sidebar.header("Filter Anomalies")

selected_countries = st.sidebar.multiselect(
    "Origin Country", options=sorted(anomalies["origin_country"].dropna().unique()), default=None)

alt_range = st.sidebar.slider(
    "Altitude Range (feet)", 0, 5000, (0, 1500))

selected_categories = st.sidebar.multiselect(
    "Aircraft Category", options=sorted(anomalies["category"].dropna().unique()), default=None)

filtered = anomalies.copy()
if selected_countries:
    filtered = filtered[filtered["origin_country"].isin(selected_countries)]
if selected_categories:
    filtered = filtered[filtered["category"].isin(selected_categories)]
filtered = filtered[
    (filtered["baro_altitude"] >= alt_range[0]) &
    (filtered["baro_altitude"] <= alt_range[1])
]

st.subheader("⚠️ Filtered Anomalous Aircraft")
st.dataframe(filtered[[
    "icao24", "origin_country", "latitude", "longitude",
    "baro_altitude", "velocity", "category", "timestamp"
]])

st.subheader("📍 Anomaly Map")
m = folium.Map(location=[38.0, -122.0], zoom_start=7)

for _, row in filtered.iterrows():
    if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=6,
            color='red',
            fill=True,
            fill_opacity=0.8,
            popup=f"⚠️ {row['icao24']} | {row['origin_country']}"
        ).add_to(m)

st_folium(m, width=1000, height=550)
