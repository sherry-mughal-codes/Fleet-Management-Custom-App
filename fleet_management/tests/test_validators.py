"""
Unit Tests for Global Validation Framework
Fleet Management System
"""

import pytest

from fleet_management.utils.exceptions import FleetValidationError
from fleet_management.validators.common_validators import (
	validate_date_range,
	validate_odometer_reading,
	validate_positive_number,
	validate_range,
	validate_required_fields,
	validate_status_transition,
)


def test_validate_positive_number():
	validate_positive_number(10, "Speed")
	validate_positive_number(0, "Odometer", allow_zero=True)

	with pytest.raises(FleetValidationError):
		validate_positive_number(-5, "Speed")

	with pytest.raises(FleetValidationError):
		validate_positive_number(0, "Speed", allow_zero=False)


def test_validate_date_range():
	validate_date_range("2026-01-01", "2026-01-10")

	with pytest.raises(FleetValidationError):
		validate_date_range("2026-01-10", "2026-01-01")


def test_validate_odometer_reading():
	validate_odometer_reading(15000, 10000, allow_rollback=False)
	validate_odometer_reading(8000, 10000, allow_rollback=True)

	with pytest.raises(FleetValidationError):
		validate_odometer_reading(8000, 10000, allow_rollback=False)


def test_validate_required_fields():
	payload = {"make": "Toyota", "model": "Corolla"}
	validate_required_fields(payload, ["make", "model"])

	with pytest.raises(FleetValidationError):
		validate_required_fields(payload, ["make", "year"])


def test_validate_range():
	validate_range(50.0, 0.0, 100.0, "Fuel Tank Level")

	with pytest.raises(FleetValidationError):
		validate_range(150.0, 0.0, 100.0, "Fuel Tank Level")


def test_validate_status_transition():
	allowed = {
		"Draft": ["Active", "Cancelled"],
		"Active": ["In Service", "Completed"]
	}
	validate_status_transition("Draft", "Active", allowed)

	with pytest.raises(FleetValidationError):
		validate_status_transition("Draft", "Completed", allowed)
