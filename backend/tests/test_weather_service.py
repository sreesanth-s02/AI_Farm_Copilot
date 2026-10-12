
import json
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services import weather_service


@pytest.fixture
def sample_weather():
    return {
        "location": {
            "latitude": 12.97,
            "longitude": 80.24,
            "timezone": "Asia/Kolkata",
        },
        "fetched_at": "2026-10-11T05:00:00+00:00",
        "current": {
            "time": "2026-10-11T10:30:00+05:30",
            "data": {
                "temperature_2m": {"value": 29.0, "unit": "°C"}
            },
        },
        "hourly": {
            "times": ["2026-10-11T11:00:00+05:30"],
            "interval_seconds": 3600,
            "data": {
                "precipitation": {"values": [1.5], "unit": "mm"}
            },
        },
    }


def test_current_weather_cache_hit(sample_weather):
    cached_data = {
        "location": sample_weather["location"],
        "fetched_at": sample_weather["fetched_at"],
        "current": sample_weather["current"],
    }

    with (
        patch.object(weather_service, "_get_cached", return_value=cached_data),
        patch.object(weather_service, "_fetch_open_meteo") as mock_fetch,
    ):
        result = weather_service.get_weather(12.97, 80.24, "current")

    assert result["cache"] == "hit"
    assert result["current"] == cached_data["current"]
    mock_fetch.assert_not_called()


def test_hourly_weather_cache_hit(sample_weather):
    cached_data = {
        "location": sample_weather["location"],
        "fetched_at": sample_weather["fetched_at"],
        "hourly": sample_weather["hourly"],
    }

    with (
        patch.object(weather_service, "_get_cached", return_value=cached_data),
        patch.object(weather_service, "_fetch_open_meteo") as mock_fetch,
    ):
        result = weather_service.get_weather(12.97, 80.24, "hourly")

    assert result["cache"] == "hit"
    assert result["hourly"] == cached_data["hourly"]
    mock_fetch.assert_not_called()


def test_current_weather_cache_miss_saves_with_correct_ttl(sample_weather):
    with (
        patch.object(weather_service, "_get_cached", return_value=None),
        patch.object(
            weather_service, "_fetch_open_meteo", return_value=sample_weather
        ) as mock_fetch,
        patch.object(weather_service, "_save_cache") as mock_save,
    ):
        result = weather_service.get_weather(12.97, 80.24, "current")

    assert result["cache"] == "miss"
    assert "current" in result
    assert "hourly" not in result
    mock_fetch.assert_called_once_with(12.97, 80.24)
    mock_save.assert_called_once()
    assert mock_save.call_args.args[2] == weather_service.CURRENT_TTL
    assert mock_save.call_args.args[1] == {
        "location": sample_weather["location"],
        "fetched_at": sample_weather["fetched_at"],
        "current": sample_weather["current"],
    }


def test_hourly_weather_cache_miss_saves_with_correct_ttl(sample_weather):
    with (
        patch.object(weather_service, "_get_cached", return_value=None),
        patch.object(
            weather_service, "_fetch_open_meteo", return_value=sample_weather
        ),
        patch.object(weather_service, "_save_cache") as mock_save,
    ):
        result = weather_service.get_weather(12.97, 80.24, "hourly")

    assert result["cache"] == "miss"
    assert "hourly" in result
    assert "current" not in result
    assert mock_save.call_args.args[2] == weather_service.HOURLY_TTL


def test_weather_fetch_failure_propagates(sample_weather):
    with (
        patch.object(weather_service, "_get_cached", return_value=None),
        patch.object(
            weather_service,
            "_fetch_open_meteo",
            side_effect=HTTPException(
                status_code=502,
                detail="Unable to retrieve weather data from Open-Meteo.",
            ),
        ),
        patch.object(weather_service, "_save_cache") as mock_save,
    ):
        with pytest.raises(HTTPException) as exc_info:
            weather_service.get_weather(12.97, 80.24, "current")

    assert exc_info.value.status_code == 502
    mock_save.assert_not_called()


def test_invalid_weather_data_type_raises_value_error():
    with pytest.raises(ValueError, match="Invalid weather data type"):
        weather_service.get_weather(12.97, 80.24, "daily")


def test_cache_key_rounds_coordinates():
    key_a = weather_service._cache_key("current", 12.97161, 80.24401)
    key_b = weather_service._cache_key("current", 12.97162, 80.24402)

    assert key_a == key_b


def test_cache_read_failure_is_treated_as_cache_miss():
    with (
        patch.object(weather_service.redis_client, "get", side_effect=RuntimeError("Redis unavailable")),
    ):
        assert weather_service._get_cached("test-weather-key") is None


def test_cache_write_failure_does_not_crash():
    with patch.object(
        weather_service.redis_client,
        "set",
        side_effect=RuntimeError("Redis unavailable"),
    ):
        weather_service._save_cache(
            "test-weather-key",
            {"temperature": 29},
            weather_service.CURRENT_TTL,
        )
