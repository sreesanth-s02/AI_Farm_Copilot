from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.field import Field
from app.models.soil import SoilReading


# Conservative software freshness rule for this prototype. It is not a
# universal agronomic validity standard.
SOIL_READING_MAX_AGE_DAYS = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _measurement(value: float | None, recorded_at: datetime | None) -> dict:
    return {
        "value": value,
        "unit": "unknown",
        "recorded_at": (
            recorded_at.isoformat() if recorded_at is not None else None
        ),
    }


def _age(recorded_at: datetime, now: datetime) -> timedelta:
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    return now - recorded_at.astimezone(timezone.utc)


def get_fertiliser_assessment(field_id: int, db: Session) -> dict:
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

    warnings: list[str] = []
    reasons: list[dict] = []
    next_steps: list[str] = []
    now = _now()

    field_details = {
        "id": field.id,
        "name": field.field_name,
        "area_acres": field.area_acres,
        "soil_type": field.soil_type,
    }
    crop_details = None
    if crop is None:
        warnings.append("No active crop is registered for this field.")
        next_steps.append("Register the current active crop before requesting advice.")
    else:
        crop_details = {
            "id": crop.id,
            "name": crop.crop_name,
            "variety": crop.variety,
            "growth_stage": crop.growth_stage,
            "status": crop.status,
        }
        reasons.append({
            "factor": "active_crop",
            "value": crop.crop_name,
            "growth_stage": crop.growth_stage,
        })

    soil_measurements = {
        "nitrogen": _measurement(
            soil.nitrogen if soil is not None else None,
            soil.recorded_at if soil is not None else None,
        ),
        "phosphorus": _measurement(
            soil.phosphorus if soil is not None else None,
            soil.recorded_at if soil is not None else None,
        ),
        "potassium": _measurement(
            soil.potassium if soil is not None else None,
            soil.recorded_at if soil is not None else None,
        ),
        "ph": _measurement(
            soil.ph if soil is not None else None,
            soil.recorded_at if soil is not None else None,
        ),
        "moisture": _measurement(
            soil.moisture if soil is not None else None,
            soil.recorded_at if soil is not None else None,
        ),
        "organic_carbon": _measurement(
            soil.organic_carbon if soil is not None else None,
            soil.recorded_at if soil is not None else None,
        ),
    }

    if soil is None:
        warnings.append("No soil reading is available.")
        warnings.extend(
            f"The latest soil reading has no {name} value."
            for name in ("nitrogen", "phosphorus", "potassium")
        )
        next_steps.append(
            "Obtain a current soil test with documented NPK units and "
            "laboratory testing method."
        )
    elif soil.recorded_at is None:
        warnings.append("The soil reading has no recorded timestamp.")
        next_steps.append(
            "Obtain a new soil test with a database-generated timestamp, "
            "documented NPK units, and laboratory testing method."
        )
    else:
        reading_age = _age(soil.recorded_at, now)
        if reading_age < timedelta(0):
            warnings.append(
                "The soil reading timestamp is in the future. "
                "Verify the device and database clocks."
            )
            next_steps.append(
                "Verify the device and database clocks, then obtain a current "
                "soil test with documented NPK units and laboratory testing method."
            )
        elif reading_age > timedelta(days=SOIL_READING_MAX_AGE_DAYS):
            warnings.append(
                "The latest soil reading is over 30 days old; "
                "refresh it before requesting a nutrient advisory."
            )
            next_steps.append(
                "Obtain a current soil test with documented NPK units and "
                "laboratory testing method."
            )

    missing_nutrients: list[str] = []
    if soil is not None:
        for name in ("nitrogen", "phosphorus", "potassium"):
            value = getattr(soil, name)
            if value is not None:
                reasons.append({
                    "factor": f"soil_{name}",
                    "value": value,
                    "unit": "unknown",
                    "recorded_at": soil.recorded_at.isoformat()
                    if soil.recorded_at is not None
                    else None,
                })
            else:
                missing_nutrients.append(name)
                warnings.append(f"The latest soil reading has no {name} value.")

    if missing_nutrients:
        warnings.append(
            "NPK data is incomplete; missing "
            + ", ".join(missing_nutrients)
            + " values are not evidence of nutrient deficiency."
        )

    if soil is not None:
        warnings.append(
            "NPK units and laboratory/testing methods are unknown unless "
            "documented with the soil test."
        )

    has_current_timestamp = (
        soil is not None
        and soil.recorded_at is not None
        and timedelta(0) <= _age(soil.recorded_at, now)
        <= timedelta(days=SOIL_READING_MAX_AGE_DAYS)
    )
    has_nutrient_measurement = (
        soil is not None
        and any(
            getattr(soil, name) is not None
            for name in ("nitrogen", "phosphorus", "potassium")
        )
    )

    if crop is None or not has_current_timestamp or not has_nutrient_measurement:
        advisory = "INSUFFICIENT_DATA"
        next_steps.append(
            "Do not apply fertiliser based on this response; obtain complete, "
            "current soil evidence with documented NPK units and testing "
            "methods, then consult a qualified agronomist before applying fertiliser."
        )
    else:
        advisory = "REVIEW_REQUIRED"
        warnings.append(
            "No validated agronomic rules are configured for interpreting these "
            "measurements."
        )
        next_steps.append(
            "Obtain or confirm a current soil test with documented NPK units and "
            "laboratory testing method before relying on the measurements."
        )
        next_steps.append(
            "Consult a qualified agronomist before applying fertiliser; have them "
            "interpret the recorded values using documented NPK units, laboratory "
            "testing method, crop, and growth stage."
        )

    return {
        "field": field_details,
        "crop": crop_details,
        "soil": {
            "reading_id": soil.id if soil is not None else None,
            "recorded_at": (
                soil.recorded_at.isoformat()
                if soil is not None and soil.recorded_at is not None
                else None
            ),
            "measurements": soil_measurements,
        },
        "advisory": advisory,
        "reasons": reasons,
        "warnings": warnings,
        "next_steps": list(dict.fromkeys(next_steps)),
        "disclaimer": (
            "This prototype does not diagnose nutrient deficiencies or prescribe "
            "fertiliser products, quantities, or schedules. Measurement units and "
            "laboratory methods are unknown unless documented separately."
        ),
    }
