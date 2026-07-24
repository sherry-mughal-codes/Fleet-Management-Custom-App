"""
Fuel Domain Whitelisted API Endpoints Implementation
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response, paginated_response
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.fuel_average_service import FuelAverageService

fuel_service = FuelService()


@api_endpoint(allow_guest=False)
def search_fuel_entries(
	vehicle: Optional[str] = None,
	employee: Optional[str] = None,
	assignment: Optional[str] = None,
	company: Optional[str] = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for searching fuel entries."""
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if employee:
		filters["employee"] = employee
	if assignment:
		filters["assignment"] = assignment
	if company:
		filters["company"] = company

	start = (page - 1) * page_length
	items = frappe.get_list(
		"Fuel Entry",
		filters=filters,
		fields=["name", "vehicle", "vehicle_number", "employee", "assignment", "fuel_date", "fuel_qty", "total_cost", "odometer", "fuel_average", "status", "company"],
		start=start,
		page_length=page_length,
		order_by="modified desc"
	)
	total_count = frappe.db.count("Fuel Entry", filters=filters) if hasattr(frappe, "db") else len(items)

	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def get_fuel_summary(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving vehicle fuel summary statistics."""
	summary = fuel_service.get_fuel_summary(vehicle)
	return success_response(data=summary, message="Fuel summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def create_fuel_entry_api(
	vehicle: str,
	fuel_qty: float,
	total_cost: float,
	odometer: float,
	company: str,
	fuel_date: Optional[str] = None,
	assignment: Optional[str] = None,
	receipt_number: Optional[str] = None,
	fuel_station_name: Optional[str] = None,
	remarks: Optional[str] = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for creating a fuel entry using minimal payload."""
	payload = {
		"vehicle": vehicle,
		"fuel_qty": fuel_qty,
		"total_cost": total_cost,
		"odometer": odometer,
		"company": company,
		"fuel_date": fuel_date,
		"assignment": assignment,
		"receipt_number": receipt_number,
		"fuel_station_name": fuel_station_name,
		"remarks": remarks
	}
	res = fuel_service.create_fuel_entry(payload)
	return success_response(data=res, message="Fuel Entry created successfully.")


@api_endpoint(allow_guest=False)
def submit_fuel_entry_api(fuel_entry_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for submitting a fuel entry and calculating fuel average."""
	res = fuel_service.submit_fuel_entry(fuel_entry_id)
	return success_response(data=res, message="Fuel Entry submitted successfully.")


@api_endpoint(allow_guest=False)
def calculate_fuel_average_api(vehicle: str, odometer: float, fuel_qty: float) -> Dict[str, Any]:
	"""Whitelisted API endpoint for calculating fuel average without saving."""
	stats = FuelAverageService.calculate_entry_average(vehicle, odometer, fuel_qty)
	return success_response(data=stats, message="Fuel average calculated successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_fuel_history_api(vehicle: str, limit: int = 20) -> Dict[str, Any]:
	"""Whitelisted API endpoint for vehicle fuel history."""
	history = fuel_service.get_vehicle_history(vehicle, limit=limit)
	return success_response(data=history, message="Vehicle fuel history retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_employee_fuel_history_api(employee: str, limit: int = 20) -> Dict[str, Any]:
	"""Whitelisted API endpoint for employee fuel history."""
	history = fuel_service.get_employee_history(employee, limit=limit)
	return success_response(data=history, message="Employee fuel history retrieved successfully.")
