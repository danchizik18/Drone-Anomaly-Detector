# 🛸 Drone Incursion Detection Dashboard

This Streamlit-based dashboard detects and visualizes anomalous aircraft activity using real-time data from the [OpenSky Network](https://opensky-network.org/). The tool is designed to support early warning systems and situational awareness for defense, aviation security, and research applications.

## 🚀 Features

- **Live Data Ingestion**: Pulls real-time ADS-B flight data from OpenSky API.
- **Anomaly Detection**: Flags potential drones or suspicious flights using rule-based heuristics (e.g., low altitude, low velocity, missing callsign, UAV category).
- **Interactive Map**: Displays anomalies on a live Folium map with popup info.
- **Custom Filtering**: Sidebar filters by altitude, country of origin, aircraft category, and location bounds.
- **Category Legend**: In-app legend to explain aircraft classification codes.
- **Manual Refresh**: User-triggered data refresh to avoid unnecessary API load.

## 🧠 Detection Logic

An aircraft is marked as **anomalous** if any of the following is true:
- Altitude < 1000 ft **and** Velocity < 50 m/s
- Missing or blank callsign
- Aircraft category code equals `8` (UAV)

## 📍 Map Popups

Each anomaly includes:
- ICAO24 hex address
- Origin country
- A link to [ADSBExchange](https://globe.adsbexchange.com) for more info

## 🔧 Tech Stack

### ⚙️ Backend
- `Python 3.9+`
- `requests` – OpenSky API data retrieval
- `pandas` – Data wrangling and CSV log management
- `os` / `datetime` – File and time operations

### 🌐 Frontend
- `Streamlit` – UI framework for interactivity
- `folium` – Map visualization
- `streamlit-folium` – Streamlit ↔ Folium integration

## 👨‍💻 Author

**Dan Chizik**  
📫 danchizik@berkeley.edu | 📍 UC Berkeley — Statistics & Data Science  
🔗 LinkedIn: https://www.linkedin.com/in/danchizik/ | 🌐 [Project Website: https://danchizikportfolio.netlify.app/



