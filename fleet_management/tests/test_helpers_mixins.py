"""
Unit Tests for Shared Helpers and Mixins
Fleet Management System
"""

import datetime
from fleet_management.utils import helpers
from fleet_management.mixins.status_mixin import StatusMixin
import pytest
from fleet_management.utils.exceptions import FleetValidationError


def test_date_helpers():
	d1 = "2026-07-01"
	d2 = "2026-07-11"
	assert helpers.get_days_between(d1, d2) == 10

	future_date = helpers.add_days_to_date("2026-07-01", 5)
	assert str(future_date) == "2026-07-06"


def test_number_helpers():
	assert helpers.round_currency(123.456) == 123.46
	assert helpers.calculate_percentage(25, 100) == 25.0
	assert helpers.calculate_percentage(10, 0) == 0.0
	assert helpers.safe_float("45.67") == 45.67
	assert helpers.safe_float("invalid", default=1.0) == 1.0


def test_string_helpers():
	assert helpers.slugify("Fleet Management Vehicle #1!") == "fleet-management-vehicle-1"
	assert helpers.sanitize_string("<script>alert('x')</script>Hello") == "alert('x')Hello"
	assert helpers.truncate("Extremely long vehicle identification string", 15) == "Extremely lon..."


def test_formatting_helpers():
	assert helpers.format_distance(12500, "KM") == "12,500 KM"
	assert helpers.format_fuel(45.5, "Liters") == "45.50 Liters"


class DummyStatusDoc(StatusMixin):
	def __init__(self, status):
		self.status = status
		self.allowed_status_transitions = {
			"Draft": ["Active"],
			"Active": ["Completed"]
		}


def test_status_mixin():
	doc = DummyStatusDoc("Draft")
	doc.validate_status_change("Active")

	with pytest.raises(FleetValidationError):
		doc.validate_status_change("Completed")
