# 🛡️ Airspace Intrusion Detection Dashboard

This Streamlit-based dashboard monitors live air traffic over the U.S. using OpenSky data and detects potential intrusions into restricted airspace zones (e.g., military bases, critical infrastructure). A basic ML model can optionally classify intrusions by risk level.

## 🔍 Features
- Live aircraft data pulled from the OpenSky Network API
- Geofencing-based intrusion detection with custom restricted zones
- ML-based intrusion risk classification (optional)
- Interactive map and intrusion logs
- Fully deployable on Streamlit Cloud

## 🛠️ Tech Stack
- **Python**, **Pandas**, **Shapely**, **Folium**
- **Streamlit** for UI
- **OpenSky API** for live air traffic data
- **Joblib** to load optional ML models

## 🚀 To Run Locally
1. Clone the repo
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the dashboard:
    ```bash
    streamlit run airspace_intrusion_predictor.py
    ```

## 📁 Logs
Detected intrusions are saved in the `logs/` directory with timestamps.

## 🤖 ML Model (Optional)
To use a classifier for `risk_level`, place a `ml_model.pkl` file in the root directory. It should accept `["velocity", "heading"]` as features.

## 📦 Deployment
This app is ready to be deployed to [Streamlit Cloud](https://streamlit.io/cloud) — just connect your GitHub repo and you're live.

---

