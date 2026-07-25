"""
API v1 - Fuel Intelligence REST Endpoints
Fleet Management System
"""

from fleet_management.api.fuel_api import (
	calculate_fuel_average_api,
	create_fuel_entry_api,
	get_employee_fuel_history_api,
	get_fuel_summary,
	get_vehicle_fuel_history_api,
	search_fuel_entries,
	submit_fuel_entry_api,
)

__all__ = [
	"search_fuel_entries",
	"get_fuel_summary",
	"create_fuel_entry_api",
	"submit_fuel_entry_api",
	"calculate_fuel_average_api",
	"get_vehicle_fuel_history_api",
	"get_employee_fuel_history_api",
]
