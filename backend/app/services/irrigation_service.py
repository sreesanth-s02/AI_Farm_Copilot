
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.field import Field
from app.models.soil import SoilReading
from app.services.weather_service import get_weather


SOIL_READING_MAX_AGE_HOURS = 24

# Prototype thresholds only; validate before real-world use.
LOW_MOISTURE_THRESHOLD = 30.0
MODERATE_MOISTURE_THRESHOLD = 50.0
EXPECTED_RAIN_THRESHOLD_MM = 2.0


def _calculate_rainfall_next_24h(weather: dict) -> float | None:
    """Sum valid hourly rainfall entries in the next 24-hour window."""
    hourly_response = weather.get("hourly", {})
    hourly_data = hourly_response.get("hourly", {})

    forecast_times = hourly_data.get("times", [])
    precipitation = (
        hourly_data.get("data", {}).get("precipitation", {})
    )
    rainfall_values = precipitation.get("values", [])

    if (
        not forecast_times
        or not rainfall_values
        or len(forecast_times) != len(rainfall_values)
    ):
        return None

    now = datetime.now().astimezone()
    window_end = now + timedelta(hours=24)
    total_rainfall = 0.0
    found_forecast = False

    for time_text, value in zip(forecast_times, rainfall_values):
        try:
            forecast_time = datetime.fromisoformat(time_text)
            rainfall = float(value)
        except (TypeError, ValueError):
            return None

        # Interpret timezone-naive timestamps in the local timezone.
        if forecast_time.tzinfo is None:
            forecast_time = forecast_time.replace(tzinfo=now.tzinfo)
        else:
            forecast_time = forecast_time.astimezone(now.tzinfo)

        if now <= forecast_time < window_end:
            if rainfall < 0:
                return None

            total_rainfall += rainfall
            found_forecast = True

    if not found_forecast:
        return None

    return round(total_rainfall, 2)


def get_irrigation_assessment(field_id: int, db: Session) -> dict:
    field = db.get(Field, field_id)

    if field is None:
        raise HTTPException(status_code=404, detail="Field not found")

    crop = db.scalars(
        select(Crop)
        .where(
            Crop.field_id == field_id,
            Crop.status == "ACTIVE",
        )
        .order_by(Crop.id.desc())
    ).first()

    soil = db.scalars(
        select(SoilReading)
        .where(SoilReading.field_id == field_id)
        .order_by(SoilReading.recorded_at.desc())
    ).first()

    warnings = []
    reasons = []
    age_hours = None

    if crop is None:
        warnings.append("No active crop is registered for this field.")

    if soil is None:
        warnings.append("No soil reading is available.")
    elif soil.recorded_at is None:
        warnings.append("The soil reading has no recorded timestamp.")
    else:
        recorded_at = soil.recorded_at

        if recorded_at.tzinfo is None:
            age_hours = (
                datetime.now() - recorded_at
            ).total_seconds() / 3600
        else:
            age_hours = (
                datetime.now(timezone.utc)
                - recorded_at.astimezone(timezone.utc)
            ).total_seconds() / 3600

        if age_hours < 0:
            warnings.append(
                "The soil reading timestamp is in the future. "
                "Verify the device and database clocks."
            )
        elif age_hours > SOIL_READING_MAX_AGE_HOURS:
            warnings.append(
                "The latest soil reading is over 24 hours old; "
                "refresh it before making an irrigation decision."
            )

    if soil is not None and soil.moisture is None:
        warnings.append("The latest soil reading has no moisture value.")

    if soil is not None and soil.moisture is not None:
        reasons.append({
            "factor": "soil_moisture",
            "value": soil.moisture,
            "unit": "%",
            "recorded_at": (
                soil.recorded_at.isoformat()
                if soil.recorded_at is not None
                else None
            ),
        })

    if crop is not None:
        reasons.append({
            "factor": "crop",
            "value": crop.crop_name,
            "growth_stage": crop.growth_stage,
        })

    weather = None

    if field.latitude is None or field.longitude is None:
        warnings.append("Field coordinates are missing.")
    else:
        try:
            weather = {
                "current": get_weather(
                    field.latitude,
                    field.longitude,
                    "current",
                ),
                "hourly": get_weather(
                    field.latitude,
                    field.longitude,
                    "hourly",
                ),
            }
        except HTTPException:
            warnings.append(
                "Weather data is temporarily unavailable."
            )

    # Calculate rainfall once and reuse it for both the decision
    # and the response summary.
    rainfall_next_24h_mm = (
        _calculate_rainfall_next_24h(weather)
        if weather is not None
        else None
    )

    if soil is None:
        advisory = "INSUFFICIENT_DATA"
        message = "Record soil moisture before assessing irrigation."

    elif soil.recorded_at is None:
        advisory = "INSUFFICIENT_DATA"
        message = "The soil reading timestamp is missing."

    elif age_hours is None or age_hours < 0:
        advisory = "INSUFFICIENT_DATA"
        message = "Verify the soil reading timestamp before proceeding."

    elif age_hours > SOIL_READING_MAX_AGE_HOURS:
        advisory = "INSUFFICIENT_DATA"
        message = (
            "The soil reading is outdated. Refresh soil moisture "
            "before making an irrigation decision."
        )

    elif soil.moisture is None:
        advisory = "INSUFFICIENT_DATA"
        message = "Record a valid soil moisture reading."

    elif not 0 <= soil.moisture <= 100:
        advisory = "INSUFFICIENT_DATA"
        message = "Soil moisture is outside the valid 0–100% range."

    elif crop is None:
        advisory = "INSUFFICIENT_DATA"
        message = "Register an active crop before assessing irrigation."

    elif weather is None:
        advisory = "INSUFFICIENT_DATA"
        message = (
            "Weather data is unavailable. Retry the assessment "
            "when the rainfall forecast is available."
        )

    elif rainfall_next_24h_mm is None:
        advisory = "INSUFFICIENT_DATA"
        message = (
            "A usable rainfall forecast is unavailable. "
            "Retry before assessing irrigation."
        )
        warnings.append(
            "The rainfall forecast could not be evaluated."
        )

    else:
        reasons.append({
            "factor": "forecast_rainfall_next_24_hours",
            "value": rainfall_next_24h_mm,
            "unit": "mm",
        })

        reasons.append({
            "factor": "prototype_moisture_thresholds",
            "low_moisture_below_percent": LOW_MOISTURE_THRESHOLD,
            "monitoring_below_percent": MODERATE_MOISTURE_THRESHOLD,
        })

        if rainfall_next_24h_mm >= EXPECTED_RAIN_THRESHOLD_MM:
            advisory = "MONITOR"
            message = (
                f"Soil moisture is {soil.moisture}%. Forecast "
                f"rainfall is {rainfall_next_24h_mm} mm over the next "
                "24 hours, meeting the prototype rain threshold. "
                "Recheck field conditions before deciding whether "
                "to irrigate."
            )

        elif soil.moisture < LOW_MOISTURE_THRESHOLD:
            advisory = "IRRIGATION_REVIEW"
            message = (
                f"Soil moisture is {soil.moisture}%, below the "
                f"prototype threshold of {LOW_MOISTURE_THRESHOLD}%. "
                f"Forecast rainfall is {rainfall_next_24h_mm} mm over "
                "the next 24 hours. Review crop needs and field "
                "conditions before irrigating."
            )

        elif soil.moisture < MODERATE_MOISTURE_THRESHOLD:
            advisory = "MONITOR"
            message = (
                f"Soil moisture is {soil.moisture}%, within the "
                f"prototype monitoring range of "
                f"{LOW_MOISTURE_THRESHOLD}% to below "
                f"{MODERATE_MOISTURE_THRESHOLD}%. Forecast rainfall "
                f"is {rainfall_next_24h_mm} mm. Continue monitoring."
            )

        else:
            advisory = "NO_IMMEDIATE_TRIGGER"
            message = (
                f"Soil moisture is {soil.moisture}%, at or above "
                f"the prototype threshold of "
                f"{MODERATE_MOISTURE_THRESHOLD}%. Forecast rainfall "
                f"is {rainfall_next_24h_mm} mm. The prototype rules "
                "do not indicate an immediate irrigation trigger."
            )

    current_weather = None

    if weather is not None:
        current_data = (
            weather.get("current", {})
            .get("current", {})
            .get("data", {})
        )

        temperature = current_data.get("temperature_2m", {})

        if temperature:
            current_weather = {
                "temperature_c": temperature.get("value"),
            }

    return {
        "field": {
            "id": field.id,
            "name": field.field_name,
        },
        "advisory": advisory,
        "message": message,
        "decision_basis": (
            "Prototype thresholds; not agronomically validated."
        ),
        "reasons": reasons,
        "warnings": warnings,
        "weather_available": weather is not None,
        "weather": {
            **(current_weather or {}),
            "rainfall_next_24h_mm": rainfall_next_24h_mm,
        } if weather is not None else None,
    }
