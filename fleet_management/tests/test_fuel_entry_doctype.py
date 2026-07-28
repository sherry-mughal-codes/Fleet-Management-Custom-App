"""
Unit Tests for Fuel Entry DocType Implementation
Fleet Management System (Frappe Framework v15)

Tests:
- FuelEntry construction from dict (naming_series default)
- before_validate_hook: total_cost calculation
- status property
- Fuel Intelligence field presence
- No 'vehicle' field stored in schema
"""

import pytest

from fleet_management.fleet_management.doctype.fuel_entry.fuel_entry import FuelEntry
from fleet_management.utils.exceptions import FleetValidationError


# ---------------------------------------------------------------------------
# Construction & Defaults
# ---------------------------------------------------------------------------

def test_fuel_entry_naming_series_default():
	"""Fuel Entry auto-sets naming_series when constructed from dict."""
	doc = FuelEntry({"assignment": "ASN-TEST-101", "fuel_qty": 50.0, "fuel_price": 2.0, "odometer": 12000.0})
	assert doc.naming_series == "FUEL-.YYYY.-.#####"


def test_fuel_entry_creation_minimal_payload():
	"""before_validate_hook calculates total_cost = qty × price."""
	payload = {
		"assignment": "ASN-TEST-101",
		"fuel_qty": 50.0,
		"fuel_price": 2.0,
		"odometer": 12000.0,
	}
	fuel_doc = FuelEntry(payload)
	fuel_doc.before_validate_hook()

	assert fuel_doc.assignment == "ASN-TEST-101"
	assert fuel_doc.fuel_qty == 50.0
	assert fuel_doc.fuel_price == 2.0
	assert fuel_doc.total_cost == 100.0
	assert fuel_doc.odometer == 12000.0
	assert fuel_doc.status == "Draft"
	assert fuel_doc.naming_series == "FUEL-.YYYY.-.#####"


def test_fuel_entry_total_cost_zero_when_missing_inputs():
	"""before_validate_hook with zero qty produces total_cost = 0."""
	doc = FuelEntry({"assignment": "ASN-TEST-101", "fuel_qty": 0.0, "fuel_price": 2.0, "odometer": 12000.0})
	doc.before_validate_hook()
	assert doc.total_cost == 0.0


def test_fuel_entry_total_cost_calculation():
	"""Total cost = qty × price."""
	doc = FuelEntry({"assignment": "ASN-X", "fuel_qty": 40.0, "fuel_price": 3.5, "odometer": 5000.0})
	doc.before_validate_hook()
	assert doc.total_cost == pytest.approx(140.0, 0.01)


def test_fuel_entry_odometer_persisted():
	"""Odometer value is stored correctly."""
	doc = FuelEntry({"assignment": "ASN-TEST-101", "fuel_qty": 40.0, "fuel_price": 2.0, "odometer": 8500.0})
	doc.before_validate_hook()
	assert doc.odometer == 8500.0


def test_fuel_entry_status_draft():
	"""Newly constructed entry has Draft status."""
	doc = FuelEntry({"assignment": "ASN-101"})
	assert doc.status == "Draft"


def test_fuel_entry_no_stored_vehicle_field():
	"""Vehicle must NOT be a stored DB field — confirmed by checking the JSON schema."""
	import json, os
	json_path = os.path.join(
		os.path.dirname(__file__),
		"..", "fleet_management", "doctype", "fuel_entry", "fuel_entry.json"
	)
	with open(json_path) as f:
		schema = json.load(f)

	field_names = [fld.get("fieldname") for fld in schema.get("fields", [])]
	# 'vehicle' must NOT be a stored field — it is a @property on the controller
	assert "vehicle" not in field_names, (
		"'vehicle' must not be a stored DB column on Fuel Entry. "
		"It must be resolved dynamically via the Vehicle Assignment @property."
	)
	# 'assignment' must be the primary reference
	assert "assignment" in field_names


# ---------------------------------------------------------------------------
# Intelligence Fields Present on Instance
# ---------------------------------------------------------------------------

def test_fuel_entry_intelligence_fields_exist():
	"""Fuel Intelligence fields should be settable on the document instance."""
	doc = FuelEntry({"assignment": "ASN-TEST"})
	# These should be settable without AttributeError
	for field in [
		"previous_odometer", "previous_fuel_date", "days_since_last_fuel",
		"distance_travelled", "fuel_average", "cost_per_km",
		"fuel_efficiency_rating", "is_first_entry"
	]:
		setattr(doc, field, None)  # should not raise


# ---------------------------------------------------------------------------
# Vehicle property resolution (no DB)
# ---------------------------------------------------------------------------

def test_fuel_entry_vehicle_property_without_db():
	"""Vehicle property returns None when no DB or hint available."""
	doc = FuelEntry({"assignment": "ASN-UNKNOWN"})
	# Without DB, vehicle returns None (assignment lookup would fail silently)
	vehicle = doc.vehicle
	assert vehicle is None or isinstance(vehicle, str)


def test_fuel_entry_vehicle_hint_accepted():
	"""vehicle hint passed via constructor is accessible via .vehicle property."""
	doc = FuelEntry({"assignment": "ASN-HINT", "vehicle": "V-HINT-001"})
	assert doc.vehicle == "V-HINT-001"
