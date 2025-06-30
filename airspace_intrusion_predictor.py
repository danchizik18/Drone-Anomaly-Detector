# airspace_intrusion_predictor.py (no geopandas version)

import requests
import pandas as pd
from shapely.geometry import Point, Polygon
from datetime import datetime
import os

# Define restricted airspace polygon (hardcoded)
# Example: small box near SF Bay Area
restricted_zones = [
    Polygon([  # zone 1
        (-122.5, 37.6),
        (-122.5, 37.8),
        (-122.3, 37.8),
        (-122.3, 37.6),
        (-122.5, 37.6)
    ])
]

# OpenSky public API columns (extended=0)
columns = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "heading", "vertical_rate", "squawk", "spi", "position_source"
]


def fetch_opensky_data():
    url = "https://opensky-network.org/api/states/all?extended=0"
    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("states"):
        df = pd.DataFrame(data["states"])

        if df.shape[1] == 17:  # Only rename if exactly 17 columns
            df.columns = [
                "icao24", "callsign", "origin_country", "time_position", "last_contact",
                "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
                "heading", "vertical_rate", "squawk", "spi", "position_source",
                "category", "other"
            ]
        else:
            print(f"[WARN] Unexpected number of columns: {df.shape[1]}")
            df.to_csv("opensky_raw_debug.csv", index=False)  # helpful for debugging
            return pd.DataFrame()  # return empty to avoid downstream errors

        df = df.dropna(subset=["latitude", "longitude", "heading"])
        df["timestamp"] = datetime.utcfromtimestamp(data["time"])
        return df

    return pd.DataFrame()



def point_within_zones(lat, lon):
    point = Point(lon, lat)
    return any(zone.contains(point) for zone in restricted_zones)


def predict_violation(row, minutes_ahead=2):
    try:
        from math import radians, cos, sin
        R = 6371000
        speed = row["velocity"] or 0
        heading = row["heading"] or 0
        lat = row["latitude"]
        lon = row["longitude"]
        distance = speed * 60 * minutes_ahead

        heading_rad = radians(heading)
        lat_rad = radians(lat)
        lon_rad = radians(lon)

        new_lat = lat + (distance / R) * (180 / 3.14159) * cos(heading_rad)
        new_lon = lon + (distance / R) * (180 / 3.14159) * sin(heading_rad) / cos(lat_rad)

        return point_within_zones(new_lat, new_lon)
    except:
        return False


def detect_intrusions(df):
    df["violation_predicted"] = df.apply(predict_violation, axis=1)
    return df[df["violation_predicted"] == True]


def log_intrusions(intrusions):
    if not intrusions.empty:
        os.makedirs("logs", exist_ok=True)
        filename = f"logs/intrusions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        intrusions.to_csv(filename, index=False)
        print(f"[INFO] Logged {len(intrusions)} intrusions to {filename}")


if __name__ == "__main__":
    print("[INFO] Fetching live aircraft data from OpenSky...")
    df = fetch_opensky_data()
    if df.empty:
        print("[WARN] No data fetched.")
    else:
        print(f"[INFO] Retrieved {len(df)} aircraft.")
        intrusions = detect_intrusions(df)
        print(f"[ALERT] Potential restricted zone violations: {len(intrusions)}")
        if not intrusions.empty:
            print(intrusions[["icao24", "callsign", "origin_country", "latitude", "longitude", "velocity", "heading", "timestamp"]])
        log_intrusions(intrusions)