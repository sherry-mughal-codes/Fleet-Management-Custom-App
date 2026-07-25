"""
Fleet Management Service Layer Package
"""
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.services.automation_service import FleetAutomationService
from fleet_management.services.base_service import BaseService
from fleet_management.services.fleet_analytics_service import FleetAnalyticsService
from fleet_management.services.fleet_cost_service import FleetCostService
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.health_service import FleetHealthService
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.settings_service import SettingsService
from fleet_management.services.vehicle_service import VehicleService

__all__ = [
	"BaseService",
	"SettingsService",
	"VehicleService",
	"AssignmentService",
	"FuelService",
	"MaintenanceService",
	"FleetCostService",
	"FleetAnalyticsService",
	"FleetHealthService",
	"FleetAutomationService",
]
