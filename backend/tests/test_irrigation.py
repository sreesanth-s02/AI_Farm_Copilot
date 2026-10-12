
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.irrigation_service import (
    get_irrigation_assessment,
)


_UNSET = object()


def make_field():
    return SimpleNamespace(
        id=1,
        field_name="North Field",
        latitude=12.9716,
        longitude=80.244,
    )


def make_crop():
    return SimpleNamespace(
        id=1,
        field_id=1,
        crop_name="Rice",
        growth_stage="Vegetative",
        status="ACTIVE",
    )


def make_soil(moisture=25.0, age_hours=1):
    return SimpleNamespace(
        field_id=1,
        moisture=moisture,
        recorded_at=datetime.now() - timedelta(hours=age_hours),
    )


def make_current_weather():
    return {
        "current": {
            "data": {
                "temperature_2m": {"value": 29.0}
            }
        }
    }


def make_hourly_weather(rainfall_values=None):
    now = datetime.now().astimezone()

    times = [
        (now + timedelta(hours=i + 1)).isoformat()
        for i in range(48)
    ]

    if rainfall_values is None:
        rainfall_values = [0.0] * 48

    if len(rainfall_values) < 48:
        rainfall_values = rainfall_values + (
            [0.0] * (48 - len(rainfall_values))
        )

    return {
        "hourly": {
            "times": times,
            "data": {
                "precipitation": {
                    "values": rainfall_values[:48],
                    "unit": "mm",
                }
            },
        }
    }


def make_db(soil=_UNSET, crop=_UNSET):
    db = MagicMock()
    db.get.return_value = make_field()

    crop_result = MagicMock()
    crop_result.first.return_value = (
        make_crop() if crop is _UNSET else crop
    )

    soil_result = MagicMock()
    soil_result.first.return_value = (
        make_soil() if soil is _UNSET else soil
    )

    db.scalars.side_effect = [crop_result, soil_result]
    return db


def test_pytest_is_working():
    assert 1 + 1 == 2


@patch("app.services.irrigation_service.get_weather")
def test_low_moisture_requires_irrigation_review(mock_weather):
    mock_weather.side_effect = [
        make_current_weather(),
        make_hourly_weather(),
    ]

    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "IRRIGATION_REVIEW"
    assert result["weather_available"] is True
    assert result["weather"]["rainfall_next_24h_mm"] == 0.0
    assert "not agronomically validated" in result["decision_basis"]


@patch("app.services.irrigation_service.get_weather")
def test_moderate_moisture_returns_monitor(mock_weather):
    mock_weather.side_effect = [
        make_current_weather(),
        make_hourly_weather(),
    ]

    db = make_db(
        soil=make_soil(moisture=40.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "MONITOR"


@patch("app.services.irrigation_service.get_weather")
def test_high_moisture_returns_no_immediate_trigger(mock_weather):
    mock_weather.side_effect = [
        make_current_weather(),
        make_hourly_weather(),
    ]

    db = make_db(
        soil=make_soil(moisture=60.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "NO_IMMEDIATE_TRIGGER"


@patch("app.services.irrigation_service.get_weather")
def test_expected_rainfall_returns_monitor(mock_weather):
    mock_weather.side_effect = [
        make_current_weather(),
        make_hourly_weather(
            rainfall_values=[
                0.0, 0.5, 0.0, 1.0, 0.0, 0.5
            ] + [0.0] * 42
        ),
    ]

    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "MONITOR"
    assert result["weather"]["rainfall_next_24h_mm"] == 2.0


def test_stale_soil_reading_returns_insufficient_data():
    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=25)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert "outdated" in result["message"].lower()
    assert result["weather_available"] is True


@patch("app.services.irrigation_service.get_weather")
def test_unavailable_weather_returns_insufficient_data(mock_weather):
    mock_weather.side_effect = HTTPException(
        status_code=502,
        detail="Weather service unavailable",
    )

    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert result["weather_available"] is False
    assert result["weather"] is None
    assert any(
        "Weather data is temporarily unavailable." in warning
        for warning in result["warnings"]
    )


def test_missing_soil_reading_returns_insufficient_data():
    db = make_db(soil=None)

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert "Record soil moisture" in result["message"]


@patch("app.services.irrigation_service.get_weather")
def test_missing_active_crop_returns_insufficient_data(mock_weather):
    mock_weather.side_effect = [
        make_current_weather(),
        make_hourly_weather(),
    ]

    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=1),
        crop=None,
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert "active crop" in result["message"].lower()


def test_nonexistent_field_returns_404():
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_irrigation_assessment(999, db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Field not found"

@pytest.mark.parametrize(
    ("rainfall_mm", "expected_advisory"),
    [
        (1.9, "IRRIGATION_REVIEW"),
        (2.0, "MONITOR"),
        (2.1, "MONITOR"),
    ],
)
@patch("app.services.irrigation_service.get_weather")
def test_rainfall_threshold_boundaries(
    mock_weather, rainfall_mm, expected_advisory
):
    mock_weather.side_effect = [
        make_current_weather(),
        make_hourly_weather(
            rainfall_values=[rainfall_mm] + [0.0] * 47
        ),
    ]

    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == expected_advisory
    assert result["weather"]["rainfall_next_24h_mm"] == rainfall_mm

@pytest.mark.parametrize("moisture", [-1.0, 100.1])
def test_invalid_soil_moisture_returns_insufficient_data(moisture):
    db = make_db(
        soil=make_soil(moisture=moisture, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert "outside the valid 0–100% range" in result["message"]

@patch("app.services.irrigation_service.get_weather")
def test_incomplete_rainfall_forecast_returns_insufficient_data(
    mock_weather,
):
    mock_weather.side_effect = [
        make_current_weather(),
        {
            "hourly": {
                "times": [],
                "data": {
                    "precipitation": {
                        "values": [],
                        "unit": "mm",
                    }
                },
            }
        },
    ]

    db = make_db(
        soil=make_soil(moisture=25.0, age_hours=1)
    )

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert result["weather_available"] is True
    assert result["weather"]["rainfall_next_24h_mm"] is None
    assert any(
        "rainfall forecast could not be evaluated" in warning.lower()
        for warning in result["warnings"]
    )


def test_future_soil_timestamp_returns_insufficient_data():
    future_soil = SimpleNamespace(
        field_id=1,
        moisture=25.0,
        recorded_at=datetime.now() + timedelta(hours=1),
    )

    db = make_db(soil=future_soil)

    result = get_irrigation_assessment(1, db)

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert "timestamp" in result["message"].lower()
    assert any(
        "future" in warning.lower()
        for warning in result["warnings"]
    )
