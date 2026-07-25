"""
Unit Tests for Maintenance DocTypes & UX Implementation
Fleet Management System
"""

import pytest

from fleet_management.fleet_management.doctype.maintenance_request.maintenance_request import (
	MaintenanceRequest,
)
from fleet_management.fleet_management.doctype.maintenance_task_template.maintenance_task_template import (
	MaintenanceTaskTemplate,
)
from fleet_management.fleet_management.doctype.maintenance_work_order.maintenance_work_order import (
	MaintenanceWorkOrder,
)
from fleet_management.utils.exceptions import FleetValidationError


def test_maintenance_request_creation_minimal():
	"""Verify Category A minimal field creation (<1 min UX velocity)."""
	payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"maintenance_type": "Preventive",
		"priority": "Medium",
		"requested_date": "2026-07-24"
	}
	req = MaintenanceRequest(payload)
	req.before_validate_hook()

	assert req.vehicle == "PROD-V-101"
	assert req.company == "Fleet Corp"
	assert req.maintenance_type == "Preventive"
	assert req.priority == "Medium"
	assert req.status == "Draft"
	assert req.naming_series == "MREQ-.YYYY.-.#####"


def test_maintenance_work_order_with_tasks():
	"""Verify Maintenance Work Order creation with Maintenance Task child table."""
	mwo_payload = {
		"vehicle": "PROD-V-101",
		"company": "Fleet Corp",
		"workshop": "Central Fleet Workshop",
		"tasks": [
			{"task_name": "Oil Change", "estimated_duration": 1.5, "completed": 0},
			{"task_name": "Brake Pad Inspection", "estimated_duration": 1.0, "completed": 0}
		]
	}
	mwo = MaintenanceWorkOrder(mwo_payload)
	mwo.before_validate_hook()

	assert mwo.vehicle == "PROD-V-101"
	assert mwo.company == "Fleet Corp"
	assert mwo.naming_series == "MWO-.YYYY.-.#####"
	assert len(mwo.tasks) == 2
	assert mwo.tasks[0].task_name == "Oil Change"


def test_maintenance_task_template():
	"""Verify Maintenance Task Template master record."""
	template_payload = {
		"task_name": "Tyre Rotation",
		"maintenance_type": "Preventive",
		"estimated_duration_hours": 0.75,
		"estimated_cost": 50.0,
		"description": "Rotate all four tyres according to cross pattern."
	}
	template = MaintenanceTaskTemplate(template_payload)
	assert template.task_name == "Tyre Rotation"
	assert template.estimated_duration_hours == 0.75


def test_maintenance_structural_validations():
	"""Verify missing mandatory fields raise FleetValidationError."""
	bad_payload = {
		"company": "Fleet Corp"
	}
	req = MaintenanceRequest(bad_payload)
	with pytest.raises(FleetValidationError):
		req.before_validate_hook()
