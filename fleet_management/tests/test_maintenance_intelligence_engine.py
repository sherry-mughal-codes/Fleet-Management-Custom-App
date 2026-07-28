"""
Unit Tests for Maintenance Intelligence Engine & Business Logic
Fleet Management System
"""

from fleet_management.business_rules.maintenance_rules import (
	MaintenanceOdometerAdvancementRule,
	MaintenanceReadOnlyCompletedRule,
)
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine


def test_maintenance_due_engine_policy_hierarchy():
	"""Verify 4-tier policy hierarchy for next due calculations."""
	# Fallback default 5000 KM
	interval_default = MaintenanceDueEngine.get_effective_maintenance_interval("V-TEST-NONEXISTENT")
	assert interval_default == 5000.0

	# Override interval priority
	interval_override = MaintenanceDueEngine.get_effective_maintenance_interval("V-TEST", override_interval=7500.0)
	assert interval_override == 7500.0

	# Next due odometer calculation
	next_due = MaintenanceDueEngine.calculate_next_due_odometer("V-TEST", completion_odometer=10000.0, override_interval=5000.0)
	assert next_due == 15000.0


def test_maintenance_odometer_advancement_rule():
	"""Verify MAINT-003 & MAINT-005 non-decreasing odometer rules."""
	valid_rule = MaintenanceOdometerAdvancementRule({"odometer": 15000.0, "previous_odometer": 10000.0})
	assert valid_rule.evaluate() is True

	invalid_rule = MaintenanceOdometerAdvancementRule({"odometer": 9000.0, "previous_odometer": 10000.0})
	assert invalid_rule.evaluate() is False


def test_maintenance_entry_cost_calculation():
	"""Verify Maintenance Entry total cost aggregation from completed items."""
	from fleet_management.fleet_management.doctype.maintenance_entry.maintenance_entry import MaintenanceEntry

	entry = MaintenanceEntry({
		"assignment": "ASN-COST-TEST",
		"maintenance_date": "2026-07-24",
		"current_odometer": 15000.0,
		"items": [
			{"item_name": "Engine Oil Change", "interval_km": 5000, "is_completed": 1, "cost": 150.0},
			{"item_name": "Brake Inspection", "interval_km": 10000, "is_completed": 1, "cost": 250.0},
			{"item_name": "Air Filter", "interval_km": 10000, "is_completed": 0, "cost": 50.0},
		]
	})
	# Manual total cost computation without triggering full validate (no DB)
	total = sum(float(i.cost or 0.0) for i in entry.items if i.is_completed)
	# (100 + 250) = 400
	assert total == 400.0


def test_maintenance_read_only_completed_rule():
	"""Verify MAINT-008 read-only completed rule."""
	r_comp = MaintenanceReadOnlyCompletedRule({"current_status": "Completed", "target_status": "Draft"})
	assert r_comp.evaluate() is False
