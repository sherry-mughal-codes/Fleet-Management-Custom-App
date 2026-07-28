"""
Fleet Management Service Layer Package
Frappe Framework v15
"""
from fleet_management.services.assignment_manager import AssignmentManager
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.services.automation_service import FleetAutomationService
from fleet_management.services.base_service import BaseService
from fleet_management.services.cost_manager import CostManager
from fleet_management.services.dashboard_manager import DashboardManager
from fleet_management.services.demo_data_manager import DemoDataManager
from fleet_management.services.demo_data_service import DemoDataService
from fleet_management.services.fleet_analytics_service import FleetAnalyticsService
from fleet_management.services.fleet_cost_service import FleetCostService
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.fuel_intelligence_service import FuelIntelligenceEngine
from fleet_management.services.fuel_manager import FuelManager
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.health_service import FleetHealthService
from fleet_management.services.maintenance_manager import MaintenanceManager
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.maintenance_template_manager import MaintenanceTemplateManager
from fleet_management.services.notification_manager import NotificationManager
from fleet_management.services.settings_service import SettingsService
from fleet_management.services.validation_manager import ValidationManager
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.services.vehicle_state_manager import VehicleStateManager, recalculate_vehicle_state

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
	"VehicleStateManager",
	"recalculate_vehicle_state",
	"AssignmentManager",
	"FuelManager",
	"MaintenanceManager",
	"MaintenanceTemplateManager",
	"CostManager",
	"DashboardManager",
	"NotificationManager",
	"ValidationManager",
	"DemoDataManager",
	"DemoDataService",
	"FuelAverageService",
	"FuelIntelligenceEngine",
]
