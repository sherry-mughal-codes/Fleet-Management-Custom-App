"""
Fleet Management REST API Version 1 (v1) Package
Provides versioned API endpoint access for all enterprise fleet sub-modules.
"""

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
	"vehicle_api",
	"assignment_api",
	"fuel_api",
	"maintenance_api",
	"cost_api",
	"analytics_api",
	"automation_api",
]
