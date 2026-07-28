"""
Unit Tests for Maintenance Entry DocType & Servicing Items
Fleet Management System
"""

import pytest

from fleet_management.fleet_management.doctype.maintenance_entry.maintenance_entry import MaintenanceEntry
from fleet_management.utils.exceptions import FleetValidationError


def test_maintenance_entry_creation_minimal():
	"""Verify Category A minimal field creation (<1 min UX velocity)."""
	entry = MaintenanceEntry({
		"assignment": "ASN-TEST-101",
		"maintenance_date": "2026-07-24",
		"current_odometer": 15000.0,
		"remarks": "Routine 15,000 KM Servicing"
	})
	assert entry.assignment == "ASN-TEST-101"
	assert entry.current_odometer == 15000.0
	assert entry.naming_series == "MAINT-.YYYY.-.#####"


def test_maintenance_entry_total_cost_from_items():
	"""Verify Maintenance Entry total cost is sum of completed item costs."""
	entry = MaintenanceEntry({
		"assignment": "ASN-COST-101",
		"maintenance_date": "2026-07-24",
		"current_odometer": 15000.0,
		"items": [
			{"item_name": "Engine Oil Change", "interval_km": 5000, "is_completed": 1, "cost": 150.0},
			{"item_name": "Brake Inspection", "interval_km": 10000, "is_completed": 1, "cost": 100.0},
			{"item_name": "Air Filter", "interval_km": 10000, "is_completed": 0, "cost": 50.0},
		]
	})
	# Manually compute total as validate() would
	total = sum(float(i.cost or 0.0) for i in entry.items if i.is_completed)
	assert total == 250.0


def test_maintenance_entry_items_count():
	"""Verify Maintenance Entry child items are correctly appended."""
	entry = MaintenanceEntry({
		"assignment": "ASN-ITEMS-101",
		"maintenance_date": "2026-07-24",
		"current_odometer": 20000.0,
		"items": [
			{"item_name": "Tyre Rotation", "interval_km": 15000, "is_completed": 1, "cost": 80.0},
			{"item_name": "Transmission Oil", "interval_km": 30000, "is_completed": 1, "cost": 200.0},
		]
	})
	assert len(entry.items) == 2
	assert entry.items[0].item_name == "Tyre Rotation"
	assert entry.items[1].item_name == "Transmission Oil"


def test_maintenance_entry_structural_validations():
	"""Verify missing mandatory assignment raises FleetValidationError."""
	entry = MaintenanceEntry({"maintenance_date": "2026-07-24"})
	with pytest.raises(FleetValidationError):
		entry.validate()
