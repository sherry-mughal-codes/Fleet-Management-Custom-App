"""
Unit Tests for Maintenance Intelligence Engine & Business Logic
Fleet Management System
"""

from fleet_management.business_rules.maintenance_rules import (
	MaintenanceOdometerAdvancementRule,
	MaintenanceReadOnlyCompletedRule,
)
from fleet_management.fleet_management.doctype.maintenance_work_order.maintenance_work_order import (
	MaintenanceWorkOrder,
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


def test_maintenance_work_order_total_cost_calculation():
	"""Verify financial cost calculation (labour + parts + external + tax - discount)."""
	mwo_payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"labour_cost": 100.0,
		"parts_cost": 250.0,
		"external_cost": 50.0,
		"tax_amount": 40.0,
		"discount_amount": 20.0
	}
	mwo = MaintenanceWorkOrder(mwo_payload)
	mwo.before_validate_hook()

	# (100 + 250 + 50 + 40) - 20 = 420.0
	assert mwo.total_cost == 420.0


def test_maintenance_read_only_completed_rule():
	"""Verify MAINT-008 read-only completed rule."""
	r_comp = MaintenanceReadOnlyCompletedRule({"current_status": "Completed", "target_status": "Draft"})
	assert r_comp.evaluate() is False
