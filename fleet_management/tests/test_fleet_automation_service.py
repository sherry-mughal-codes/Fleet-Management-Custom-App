"""
Unit Tests for Fleet Automation Service Engine
Fleet Management System
"""

from fleet_management.services.automation_service import FleetAutomationService


def test_automation_service_instantiation():
	"""Verify service instantiation and domain subservices binding."""
	service = FleetAutomationService()
	assert service.vehicle_service is not None
	assert service.assignment_service is not None
	assert service.fuel_service is not None
	assert service.maintenance_service is not None
	assert service.cost_service is not None
	assert service.health_service is not None


def test_maintenance_automation_run():
	"""Verify maintenance automation subroutine executes cleanly."""
	service = FleetAutomationService()
	res = service.run_maintenance_automation()
	assert "upcoming_count" in res
	assert "overdue_count" in res
	assert "reminders_sent" in res


def test_fuel_automation_run():
	"""Verify fuel automation subroutine executes cleanly."""
	service = FleetAutomationService()
	res = service.run_fuel_automation()
	assert "anomalies_detected" in res
	assert "declining_count" in res
	assert "inactive_fuel_vehicles" in res


def test_assignment_automation_run():
	"""Verify assignment automation subroutine executes cleanly."""
	service = FleetAutomationService()
	res = service.run_assignment_automation()
	assert "expiring_count" in res
	assert "inactive_count" in res
	assert "notifications_sent" in res


def test_cost_automation_run():
	"""Verify cost automation subroutine executes cleanly."""
	service = FleetAutomationService()
	res = service.run_cost_automation()
	assert "status" in res


def test_health_monitoring_automation_run():
	"""Verify health monitoring automation subroutine executes cleanly."""
	service = FleetAutomationService()
	res = service.run_health_monitoring_automation()
	assert "status" in res
	assert "health_score" in res


def test_run_all_automations():
	"""Verify master orchestrator executes all subroutines."""
	service = FleetAutomationService()
	summary = service.run_all_automations()
	assert summary["status"] in ["completed", "skipped", "success"]
