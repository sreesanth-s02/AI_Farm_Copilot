from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.fertiliser_service import get_fertiliser_assessment


def make_field():
    return SimpleNamespace(
        id=1,
        field_name="North Field",
        area_acres=12.5,
        soil_type="Loam",
    )


def make_crop():
    return SimpleNamespace(
        id=1,
        field_id=1,
        crop_name="Rice",
        variety="IR64",
        growth_stage="Vegetative",
        status="ACTIVE",
    )


def make_soil(**overrides):
    values = {
        "id": 10,
        "field_id": 1,
        "nitrogen": 40.0,
        "phosphorus": 20.0,
        "potassium": 30.0,
        "ph": 6.5,
        "moisture": 25.0,
        "organic_carbon": 1.2,
        "recorded_at": datetime(2026, 10, 10, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


_DEFAULT = object()


def make_db(*, crop=_DEFAULT, soil=_DEFAULT):
    db = MagicMock()
    db.get.return_value = make_field()
    crop_result = MagicMock()
    crop_result.first.return_value = (
        make_crop() if crop is _DEFAULT else crop
    )
    soil_result = MagicMock()
    soil_result.first.return_value = (
        make_soil() if soil is _DEFAULT else (
            None if soil is None else make_soil(**soil)
        )
    )
    db.scalars.side_effect = [crop_result, soil_result]
    return db


def assess(db):
    with patch(
        "app.services.fertiliser_service._now",
        return_value=datetime(2026, 10, 20, tzinfo=timezone.utc),
    ):
        return get_fertiliser_assessment(1, db)


def test_field_not_found():
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(HTTPException) as error:
        get_fertiliser_assessment(999, db)

    assert error.value.status_code == 404
    assert error.value.detail == "Field not found"


def test_no_active_crop_returns_insufficient_data():
    result = assess(make_db(crop=None))

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert any("No active crop" in warning for warning in result["warnings"])


def test_no_soil_reading_returns_insufficient_data():
    result = assess(make_db(soil=None))

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert "No soil reading is available." in result["warnings"]
    for nutrient in ("nitrogen", "phosphorus", "potassium"):
        assert any(nutrient in warning for warning in result["warnings"])
    assert any("documented NPK units" in step for step in result["next_steps"])


def test_stale_reading_returns_insufficient_data():
    result = assess(make_db(soil={"recorded_at": datetime(2026, 9, 19, tzinfo=timezone.utc)}))

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert any("over 30 days old" in warning for warning in result["warnings"])


def test_future_reading_returns_insufficient_data():
    result = assess(make_db(soil={"recorded_at": datetime(2026, 10, 21, tzinfo=timezone.utc)}))

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert any("future" in warning for warning in result["warnings"])


def test_missing_npk_values_returns_insufficient_data():
    result = assess(make_db(soil={
        "nitrogen": None,
        "phosphorus": None,
        "potassium": None,
    }))

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert result["soil"]["measurements"]["nitrogen"]["value"] is None
    for nutrient in ("nitrogen", "phosphorus", "potassium"):
        assert any(f"no {nutrient} value" in warning for warning in result["warnings"])
    assert any("not evidence of nutrient deficiency" in warning for warning in result["warnings"])


@pytest.mark.parametrize(
    ("available", "missing"),
    [
        ("nitrogen", ("phosphorus", "potassium")),
        ("phosphorus", ("nitrogen", "potassium")),
        ("potassium", ("nitrogen", "phosphorus")),
    ],
)
def test_partial_npk_readings_identify_missing_values(available, missing):
    result = assess(make_db(soil={
        "nitrogen": 40.0 if available == "nitrogen" else None,
        "phosphorus": 20.0 if available == "phosphorus" else None,
        "potassium": 30.0 if available == "potassium" else None,
    }))

    assert result["advisory"] == "REVIEW_REQUIRED"
    assert result["soil"]["measurements"][available]["value"] is not None
    for nutrient in missing:
        assert result["soil"]["measurements"][nutrient]["value"] is None
        assert any(
            f"no {nutrient} value" in warning
            for warning in result["warnings"]
        )
    assert any("not evidence of nutrient deficiency" in warning for warning in result["warnings"])
    assert any("units and laboratory/testing methods are unknown" in warning for warning in result["warnings"])
    assert any("qualified agronomist" in step for step in result["next_steps"])


def test_usable_measurements_require_expert_review():
    result = assess(make_db(soil={
        "recorded_at": datetime(2026, 10, 19, tzinfo=timezone.utc),
        "nitrogen": 40.0,
        "phosphorus": None,
        "potassium": None,
    }))

    assert result["advisory"] == "REVIEW_REQUIRED"
    assert result["soil"]["measurements"]["nitrogen"]["unit"] == "unknown"
    assert any("No validated agronomic rules" in warning for warning in result["warnings"])
    assert any("qualified agronomist" in step for step in result["next_steps"])
    assert any("documented NPK units" in step for step in result["next_steps"])


def test_valid_response_structure():
    result = assess(make_db())

    assert set(result) == {
        "field",
        "crop",
        "soil",
        "advisory",
        "reasons",
        "warnings",
        "next_steps",
        "disclaimer",
    }
    assert result["field"]["name"] == "North Field"
    assert result["crop"]["name"] == "Rice"
    assert set(result["soil"]["measurements"]) == {
        "nitrogen",
        "phosphorus",
        "potassium",
        "ph",
        "moisture",
        "organic_carbon",
    }
    assert result["advisory"] == "REVIEW_REQUIRED"


def test_missing_timestamp_returns_insufficient_data():
    result = assess(make_db(soil={"recorded_at": None}))

    assert result["advisory"] == "INSUFFICIENT_DATA"
    assert any("no recorded timestamp" in warning for warning in result["warnings"])
