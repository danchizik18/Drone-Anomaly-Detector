import requests
import pandas as pd
import time
from datetime import datetime
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

load_dotenv()


def get_access_token(client_id, client_secret):
    token_url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(token_url, headers=headers, data=data)
    return response.json().get("access_token")

def fetch_opensky_data(token):
    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": 37.5,  # CA region
        "lamax": 39.0,
        "lomin": -123.0,
        "lomax": -121.0,
        "extended": 1
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params)
    return response.json()


def log_aircraft_data(data):
    if data.get("states") is None:
        return
    columns = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "heading", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source", "category"  
  ]

    df = pd.DataFrame(data["states"], columns=columns)
    df["timestamp"] = datetime.utcfromtimestamp(data["time"]).strftime('%Y-%m-%d %H:%M:%S')
    df.to_csv("data/flight_logs.csv", mode='a', index=False, header=False)


if __name__ == "__main__":
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    token = get_access_token(client_id, client_secret)

    for _ in range(5):
        try:
            data = fetch_opensky_data(token)
            log_aircraft_data(data)
            print("Logged aircraft data at", datetime.utcnow())
        except Exception as e:
            print("Error:", e)

        time.sleep(30)  
