"""
Fleet Management API Layer Package
"""
from fleet_management.api.base import api_endpoint, boot_session
from fleet_management.api import (
	vehicle_api,
	assignment_api,
	fuel_api,
	maintenance_api,
	cost_api,
	analytics_api,
	automation_api,
)

__all__ = [
	"api_endpoint",
	"boot_session",
	"vehicle_api",
	"assignment_api",
	"fuel_api",
	"maintenance_api",
	"cost_api",
	"analytics_api",
	"automation_api",
]
