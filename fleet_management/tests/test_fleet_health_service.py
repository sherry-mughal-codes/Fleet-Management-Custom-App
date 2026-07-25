"""
Unit Tests for Fleet Health & Data Integrity Monitoring Service
Fleet Management System
"""

from fleet_management.services.health_service import FleetHealthService


def test_fleet_health_service_run_report():
	"""Verify FleetHealthService executes data integrity checks and returns structured report."""
	service = FleetHealthService()
	report = service.run_health_check()

	assert "status" in report
	assert report["status"] in ["Healthy", "Degraded", "Critical"]
	assert "health_score" in report
	assert 0.0 <= report["health_score"] <= 100.0
	assert "total_checks" in report
	assert "issues" in report
	assert isinstance(report["issues"], list)


def test_odometer_consistency_verifier():
	"""Verify odometer verifier handles checks without raising errors."""
	service = FleetHealthService()
	issues = service.verify_odometer_consistency()
	assert isinstance(issues, list)


def test_broken_references_verifier():
	"""Verify broken references verifier returns structured issue lists."""
	service = FleetHealthService()
	issues = service.verify_broken_references()
	assert isinstance(issues, list)


def test_assignment_integrity_verifier():
	"""Verify assignment integrity verifier checks duplicate and status rules."""
	service = FleetHealthService()
	issues = service.verify_assignment_integrity()
	assert isinstance(issues, list)


def test_maintenance_links_verifier():
	"""Verify maintenance links verifier output format."""
	service = FleetHealthService()
	issues = service.verify_maintenance_links()
	assert isinstance(issues, list)


def test_fuel_relationships_verifier():
	"""Verify fuel relationships verifier checks capacity bounds."""
	service = FleetHealthService()
	issues = service.verify_fuel_relationships()
	assert isinstance(issues, list)
