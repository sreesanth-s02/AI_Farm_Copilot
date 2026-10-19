
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db


client = TestClient(app)


def test_irrigation_api_returns_assessment():
    mock_db = MagicMock()

    with (
        patch(
            "app.api.recommendations.get_irrigation_assessment"
        ) as mock_assessment,
    ):
        mock_assessment.return_value = {
            "field": {"id": 1, "name": "North Field"},
            "advisory": "IRRIGATION_REVIEW",
            "message": "Review field conditions before irrigating.",
            "decision_basis": (
                "Prototype thresholds; not agronomically validated."
            ),
            "reasons": [],
            "warnings": [],
            "weather_available": True,
            "weather": {
                "temperature_c": 29.0,
                "rainfall_next_24h_mm": 0.0,
            },
        }

        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            response = client.get(
                "/api/v1/recommendations/irrigation/1"
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()
    assert body["field"]["id"] == 1
    assert body["advisory"] == "IRRIGATION_REVIEW"
    assert "message" in body
    assert "reasons" in body
    assert "warnings" in body
    assert "weather" in body

    mock_assessment.assert_called_once_with(1, mock_db)


def test_irrigation_api_returns_404_for_missing_field():
    with patch(
        "app.api.recommendations.get_irrigation_assessment"
    ) as mock_assessment:
        from fastapi import HTTPException

        mock_assessment.side_effect = HTTPException(
            status_code=404,
            detail="Field not found",
        )

        app.dependency_overrides[get_db] = lambda: MagicMock()

        try:
            response = client.get(
                "/api/v1/recommendations/irrigation/999"
            )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Field not found"

def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_invalid_field_id_returns_422():
    response = client.get(
        "/api/v1/recommendations/irrigation/abc"
    )

    assert response.status_code == 422

from unittest.mock import patch


def test_database_health_connected():
    with patch("app.main.engine.connect") as mock_connect:
        mock_connection = MagicMock()
        mock_connect.return_value.__enter__.return_value = (
            mock_connection
        )

        response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {
        "database": "MySQL",
        "status": "connected",
    }
    mock_connection.execute.assert_called_once()


def test_database_health_error():
    with patch(
        "app.main.engine.connect",
        side_effect=Exception("Database unavailable"),
    ):
        response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json()["database"] == "MySQL"
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "Database unavailable"

from datetime import datetime
from types import SimpleNamespace


def test_create_farmer_success():
    mock_db = MagicMock()
    mock_db.scalar.return_value = None

    mock_db.refresh.side_effect = lambda farmer: (
        setattr(farmer, "id", 1),
        setattr(farmer, "created_at", datetime(2026, 10, 11, 10, 0, 0)),
    )

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/farmers",
            json={
                "name": "Test Farmer",
                "phone": "9876543210",
                "preferred_language": "ta",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Test Farmer"
    assert body["phone"] == "9876543210"
    assert body["preferred_language"] == "ta"
    assert "created_at" in body

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_create_farmer_duplicate_phone_returns_409():
    mock_db = MagicMock()
    mock_db.scalar.return_value = SimpleNamespace(
        id=1,
        phone="9876543210",
    )

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/farmers",
            json={
                "name": "Test Farmer",
                "phone": "9876543210",
                "preferred_language": "ta",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_farmer_invalid_language_returns_422():
    response = client.post(
        "/api/v1/farmers",
        json={
            "name": "Test Farmer",
            "phone": "9876543210",
            "preferred_language": "invalid",
        },
    )

    assert response.status_code == 422


def test_get_farmer_not_found_returns_404():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/farmers/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"

def test_create_farm_success():
    mock_db = MagicMock()
    mock_db.get.return_value = SimpleNamespace(id=1)

    def populate_farm(farm):
        farm.id = 10
        farm.created_at = datetime(2026, 10, 11, 10, 0, 0)

    mock_db.refresh.side_effect = populate_farm

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/farms",
            json={
                "farmer_id": 1,
                "farm_name": "North Farm",
                "district": "Chennai",
                "village": "Example Village",
                "total_area_acres": 2.5,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 10
    assert body["farmer_id"] == 1
    assert body["farm_name"] == "North Farm"
    assert body["district"] == "Chennai"
    assert body["total_area_acres"] == 2.5
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_create_farm_farmer_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/farms",
            json={
                "farmer_id": 999,
                "farm_name": "North Farm",
                "district": "Chennai",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"


def test_get_farm_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/farms/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_get_farmer_farms_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/farms/farmer/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"

def test_create_field_success():
    mock_db = MagicMock()
    mock_db.get.return_value = SimpleNamespace(id=1)

    def populate_field(field):
        field.id = 5

    mock_db.refresh.side_effect = populate_field

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/fields",
            json={
                "farm_id": 1,
                "field_name": "North Field",
                "area_acres": 2.5,
                "soil_type": "Clay",
                "latitude": 12.9716,
                "longitude": 80.244,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 5
    assert body["farm_id"] == 1
    assert body["field_name"] == "North Field"
    assert body["area_acres"] == 2.5
    assert body["latitude"] == 12.9716
    assert body["longitude"] == 80.244

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_create_field_farm_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/fields",
            json={
                "farm_id": 999,
                "field_name": "North Field",
                "area_acres": 2.5,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_create_field_invalid_area_returns_422():
    response = client.post(
        "/api/v1/fields",
        json={
            "farm_id": 1,
            "field_name": "North Field",
            "area_acres": 0,
        },
    )

    assert response.status_code == 422


def test_get_field_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/fields/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Field not found"

def test_create_crop_success():
    mock_db = MagicMock()
    mock_db.get.return_value = SimpleNamespace(id=5)

    def populate_crop(crop):
        crop.id = 20

    mock_db.refresh.side_effect = populate_crop

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/crops",
            json={
                "field_id": 5,
                "crop_name": "Rice",
                "variety": "Ponni",
                "sowing_date": "2026-06-01",
                "expected_harvest_date": "2026-10-01",
                "growth_stage": "Vegetative",
                "status": "ACTIVE",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 20
    assert body["field_id"] == 5
    assert body["crop_name"] == "Rice"
    assert body["variety"] == "Ponni"
    assert body["sowing_date"] == "2026-06-01"
    assert body["status"] == "ACTIVE"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_create_crop_field_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/crops",
            json={
                "field_id": 999,
                "crop_name": "Rice",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Field not found"


def test_create_crop_invalid_date_returns_422():
    response = client.post(
        "/api/v1/crops",
        json={
            "field_id": 5,
            "crop_name": "Rice",
            "sowing_date": "not-a-date",
        },
    )

    assert response.status_code == 422


def test_get_crop_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/crops/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found"

def test_create_soil_reading_success():
    mock_db = MagicMock()
    mock_db.get.return_value = SimpleNamespace(id=1)

    def populate_reading(reading):
        reading.id = 30
        reading.recorded_at = datetime(2026, 10, 11, 10, 0, 0)

    mock_db.refresh.side_effect = populate_reading

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/soil",
            json={
                "field_id": 1,
                "nitrogen": 40,
                "phosphorus": 20,
                "potassium": 30,
                "ph": 6.5,
                "moisture": 25,
                "organic_carbon": 1.2,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 30
    assert body["field_id"] == 1
    assert body["nitrogen"] == 40
    assert body["ph"] == 6.5
    assert body["moisture"] == 25
    assert "recorded_at" in body

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_create_soil_reading_field_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/soil",
            json={
                "field_id": 999,
                "moisture": 25,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Field not found"


def test_create_soil_reading_invalid_moisture_returns_422():
    response = client.post(
        "/api/v1/soil",
        json={
            "field_id": 1,
            "moisture": 101,
        },
    )

    assert response.status_code == 422


def test_create_soil_reading_client_timestamp_returns_422():
    response = client.post(
        "/api/v1/soil",
        json={
            "field_id": 1,
            "moisture": 25,
            "recorded_at": "2026-10-20T00:00:00",
        },
    )

    assert response.status_code == 422


def test_get_soil_reading_not_found():
    mock_db = MagicMock()
    mock_db.get.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/soil/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Soil reading not found"

def test_current_weather_api_success():
    mock_weather = {
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
        "cache": "miss",
    }

    with patch("app.api.weather.get_weather", return_value=mock_weather) as mock_get:
        response = client.get(
            "/api/v1/weather/current",
            params={"latitude": 12.97, "longitude": 80.24},
        )

    assert response.status_code == 200
    assert response.json()["current"]["data"]["temperature_2m"]["value"] == 29.0
    assert response.json()["cache"] == "miss"
    mock_get.assert_called_once_with(
        latitude=12.97,
        longitude=80.24,
        data_type="current",
    )


def test_hourly_weather_api_success():
    mock_weather = {
        "location": {
            "latitude": 12.97,
            "longitude": 80.24,
            "timezone": "Asia/Kolkata",
        },
        "fetched_at": "2026-10-11T05:00:00+00:00",
        "hourly": {
            "times": ["2026-10-11T11:00:00+05:30"],
            "interval_seconds": 3600,
            "data": {
                "precipitation": {
                    "values": [2.5],
                    "unit": "mm",
                }
            },
        },
        "cache": "hit",
    }

    with patch("app.api.weather.get_weather", return_value=mock_weather) as mock_get:
        response = client.get(
            "/api/v1/weather/hourly",
            params={"latitude": 12.97, "longitude": 80.24},
        )

    assert response.status_code == 200
    assert response.json()["hourly"]["data"]["precipitation"]["values"] == [2.5]
    assert response.json()["cache"] == "hit"
    mock_get.assert_called_once_with(
        latitude=12.97,
        longitude=80.24,
        data_type="hourly",
    )


def test_current_weather_rejects_invalid_latitude():
    response = client.get(
        "/api/v1/weather/current",
        params={"latitude": 91, "longitude": 80.24},
    )

    assert response.status_code == 422


def test_hourly_weather_rejects_invalid_longitude():
    response = client.get(
        "/api/v1/weather/hourly",
        params={"latitude": 12.97, "longitude": 181},
    )

    assert response.status_code == 422


def test_current_weather_requires_coordinates():
    response = client.get("/api/v1/weather/current")

    assert response.status_code == 422


def test_hourly_weather_requires_coordinates():
    response = client.get(
        "/api/v1/weather/hourly",
        params={"latitude": 12.97},
    )

    assert response.status_code == 422


def test_current_weather_provider_failure_returns_502():
    from fastapi import HTTPException

    with patch(
        "app.api.weather.get_weather",
        side_effect=HTTPException(
            status_code=502,
            detail="Unable to retrieve weather data from Open-Meteo.",
        ),
    ):
        response = client.get(
            "/api/v1/weather/current",
            params={"latitude": 12.97, "longitude": 80.24},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Unable to retrieve weather data from Open-Meteo."
    )
