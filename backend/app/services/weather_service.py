
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import openmeteo_requests
from fastapi import HTTPException

from app.db.redis_client import redis_client

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

CURRENT_TTL = 900
HOURLY_TTL = 3600

CURRENT_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "wind_speed_10m",
]

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "precipitation_probability",
    "rain",
    "wind_speed_10m",
    "et0_fao_evapotranspiration",
]

UNITS = {
    "temperature_2m": "°C",
    "relative_humidity_2m": "%",
    "precipitation": "mm",
    "rain": "mm",
    "wind_speed_10m": "km/h",
    "precipitation_probability": "%",
    "et0_fao_evapotranspiration": "mm",
}


def _cache_key(data_type: str, latitude: float, longitude: float) -> str:
    return (
        f"ai_farm_copilot:weather:v2:{data_type}:"
        f"{round(latitude, 4)}:{round(longitude, 4)}"
    )


def _get_cached(key: str):
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


def _save_cache(key: str, data: dict, ttl: int) -> None:
    try:
        redis_client.set(key, json.dumps(data), ex=ttl)
    except Exception:
        pass


def _fetch_open_meteo(latitude: float, longitude: float) -> dict:
    client = openmeteo_requests.Client()

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "current": CURRENT_VARIABLES,
        "hourly": HOURLY_VARIABLES,
        "forecast_days": 2,
    }

    try:
        response = client.weather_api(
            OPEN_METEO_URL, params=params
        )[0]

        timezone_name = response.Timezone().decode("utf-8")
        local_timezone = ZoneInfo(timezone_name)

        current = response.Current()
        hourly = response.Hourly()

        current_data = {}
        for index, name in enumerate(CURRENT_VARIABLES):
            variable = current.Variables(index)
            current_data[name] = {
                "value": variable.Value(),
                "unit": UNITS[name],
            }

        hourly_timestamps = list(
            range(
                hourly.Time(),
                hourly.TimeEnd(),
                hourly.Interval(),
            )
        )

        hourly_times = [
            datetime.fromtimestamp(timestamp, local_timezone).isoformat()
            for timestamp in hourly_timestamps
        ]

        hourly_data = {}
        for index, name in enumerate(HOURLY_VARIABLES):
            variable = hourly.Variables(index)
            hourly_data[name] = {
                "values": variable.ValuesAsNumpy().tolist(),
                "unit": UNITS[name],
            }

        return {
            "location": {
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "timezone": timezone_name,
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "current": {
                "time": datetime.fromtimestamp(
                    current.Time(), local_timezone
                ).isoformat(),
                "data": current_data,
            },
            "hourly": {
                "times": hourly_times,
                "interval_seconds": hourly.Interval(),
                "data": hourly_data,
            },
        }

    except Exception as exc:
        print(
            f"Open-Meteo fetch error: "
            f"{type(exc).__name__}: {exc}"
        )
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve weather data from Open-Meteo.",
        ) from exc


def get_weather(
    latitude: float,
    longitude: float,
    data_type: str,
) -> dict:
    if data_type not in {"current", "hourly"}:
        raise ValueError("Invalid weather data type")

    key = _cache_key(data_type, latitude, longitude)
    cached = _get_cached(key)

    if cached is not None:
        return {**cached, "cache": "hit"}

    weather = _fetch_open_meteo(latitude, longitude)

    if data_type == "current":
        result = {
            "location": weather["location"],
            "fetched_at": weather["fetched_at"],
            "current": weather["current"],
        }
        ttl = CURRENT_TTL
    else:
        result = {
            "location": weather["location"],
            "fetched_at": weather["fetched_at"],
            "hourly": weather["hourly"],
        }
        ttl = HOURLY_TTL

    _save_cache(key, result, ttl)

    return {**result, "cache": "miss"}
