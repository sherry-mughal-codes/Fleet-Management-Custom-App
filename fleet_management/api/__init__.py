"""
Fleet Management API Layer Package
"""
from fleet_management.api import (
	analytics_api,
	assignment_api,
	automation_api,
	cost_api,
	fuel_api,
	maintenance_api,
	v1,
	vehicle_api,
)
from fleet_management.api.base import api_endpoint, boot_session

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
	"v1",
]
