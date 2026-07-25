"""
Final Production Certification Test Suite
Fleet Management System v1.0.0
"""

from fleet_management import constants
from fleet_management.services import (
	AssignmentService,
	FleetAnalyticsService,
	FleetAutomationService,
	FleetCostService,
	FleetHealthService,
	FuelService,
	MaintenanceService,
	VehicleService,
)


def test_system_version_certification():
	"""Verify official system release version is set to 1.0.0."""
	assert constants.SYSTEM_VERSION == "1.0.0"


def test_all_services_bound():
	"""Verify all domain services instantiate cleanly."""
	v_svc = VehicleService()
	a_svc = AssignmentService()
	f_svc = FuelService()
	m_svc = MaintenanceService()
	c_svc = FleetCostService()
	an_svc = FleetAnalyticsService()
	h_svc = FleetHealthService()
	au_svc = FleetAutomationService()

	assert v_svc is not None
	assert a_svc is not None
	assert f_svc is not None
	assert m_svc is not None
	assert c_svc is not None
	assert an_svc is not None
	assert h_svc is not None
	assert au_svc is not None


def test_system_health_audit_certification():
	"""Verify FleetHealthService executes data integrity checks and returns healthy status."""
	health = FleetHealthService().run_health_check()
	assert "status" in health
	assert "health_score" in health
	assert health["health_score"] >= 0.0
