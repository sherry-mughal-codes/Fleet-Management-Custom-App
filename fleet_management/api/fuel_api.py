"""
Fuel Domain Whitelisted API Endpoints
Fleet Management System (Frappe Framework v15)

All endpoints are assignment-driven.
No direct vehicle column exists on Fuel Entry.
"""

from typing import Any, Dict

import frappe

from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import paginated_response, success_response
from fleet_management.services.fuel_average_service import FuelAverageService
from fleet_management.services.fuel_intelligence_service import FuelIntelligenceEngine
from fleet_management.services.fuel_service import FuelService

fuel_service = FuelService()


# ---------------------------------------------------------------------------
# Fuel Context — Called by client script on assignment selection
# ---------------------------------------------------------------------------

@api_endpoint(allow_guest=False)
def get_assignment_fuel_context(assignment: str) -> Dict[str, Any]:
	"""
	Called when a Vehicle Assignment is selected on the Fuel Entry form.
	Returns:
	  - smart_odometer: best odometer reading for the new entry
	  - previous_fuel_record: previous submitted Fuel Entry (or null if first)
	  - is_first_entry: boolean
	"""
	if not frappe.db.exists("Vehicle Assignment", assignment):
		return success_response(data={}, message="Assignment not found.")

	vehicle_id = frappe.db.get_value("Vehicle Assignment", assignment, "vehicle")

	smart_odo = FuelIntelligenceEngine.get_smart_odometer(assignment, vehicle_id)
	prev = FuelIntelligenceEngine.get_previous_fuel_record(vehicle_id) if vehicle_id else None

	return success_response(
		data={
			"smart_odometer": smart_odo,
			"is_first_entry": prev is None,
			"previous_fuel_record": prev,
		},
		message="Assignment fuel context retrieved."
	)


# ---------------------------------------------------------------------------
# Fuel Intelligence — Called when qty/price change on client
# ---------------------------------------------------------------------------

@api_endpoint(allow_guest=False)
def calculate_fuel_intelligence_api(
	assignment: str,
	current_odometer: float,
	fuel_qty: float,
	fuel_price: float,
	fuel_date: str | None = None,
	exclude_entry: str | None = None
) -> Dict[str, Any]:
	"""
	Calculates and returns all Fuel Intelligence metrics for the current form values.
	Used by the client script on qty/price change without saving the document.
	"""
	if not frappe.db.exists("Vehicle Assignment", assignment):
		return success_response(data={}, message="Assignment not found.")

	vehicle_id = frappe.db.get_value("Vehicle Assignment", assignment, "vehicle")
	if not vehicle_id:
		return success_response(data={}, message="Could not resolve vehicle from assignment.")

	intel = FuelIntelligenceEngine.calculate_intelligence(
		vehicle_id=vehicle_id,
		current_odometer=float(current_odometer or 0.0),
		fuel_qty=float(fuel_qty or 0.0),
		fuel_price=float(fuel_price or 0.0),
		fuel_date=fuel_date or frappe.utils.nowdate(),
		exclude_entry=exclude_entry,
	)

	return success_response(data=intel, message="Fuel intelligence calculated.")


# ---------------------------------------------------------------------------
# Standard CRUD / Query Endpoints
# ---------------------------------------------------------------------------

@api_endpoint(allow_guest=False)
def search_fuel_entries(
	assignment: str | None = None,
	company: str | None = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Search fuel entries — no direct vehicle filter (not a stored column)."""
	filters: Dict[str, Any] = {}
	if assignment:
		filters["assignment"] = assignment

	start = (page - 1) * page_length
	items = frappe.get_list(
		"Fuel Entry",
		filters=filters,
		fields=["name", "assignment", "fuel_date", "fuel_qty", "total_cost",
		        "odometer", "fuel_average", "fuel_efficiency_rating", "docstatus"],
		start=start,
		page_length=page_length,
		order_by="modified desc"
	)
	total_count = frappe.db.count("Fuel Entry", filters=filters) if hasattr(frappe, "db") else len(items)

	# If company filter requested, join-filter in Python (no company column on FE)
	if company:
		def entry_matches_company(e):
			asn = e.get("assignment")
			if not asn:
				return False
			co = frappe.db.get_value("Vehicle Assignment", asn, "company")
			return co == company
		items = [e for e in items if entry_matches_company(e)]

	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def get_fuel_summary(vehicle: str) -> Dict[str, Any]:
	"""Fuel summary statistics for a vehicle."""
	summary = fuel_service.get_fuel_summary(vehicle)
	return success_response(data=summary, message="Fuel summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def create_fuel_entry_api(
	assignment: str,
	fuel_qty: float,
	fuel_price: float,
	odometer: float,
	fuel_date: str | None = None,
	receipt_number: str | None = None,
	fuel_station_name: str | None = None,
	remarks: str | None = None
) -> Dict[str, Any]:
	"""Creates a Fuel Entry using minimal payload (assignment-driven)."""
	payload = {
		"assignment": assignment,
		"fuel_qty": fuel_qty,
		"fuel_price": fuel_price,
		"odometer": odometer,
		"fuel_date": fuel_date or frappe.utils.nowdate(),
	}
	if receipt_number:
		payload["receipt_number"] = receipt_number
	if fuel_station_name:
		payload["fuel_station_name"] = fuel_station_name
	if remarks:
		payload["remarks"] = remarks

	res = fuel_service.create_fuel_entry(payload)
	return success_response(data=res, message="Fuel Entry created successfully.")


@api_endpoint(allow_guest=False)
def submit_fuel_entry_api(fuel_entry_id: str) -> Dict[str, Any]:
	"""Submits a fuel entry and triggers all downstream calculations."""
	res = fuel_service.submit_fuel_entry(fuel_entry_id)
	return success_response(data=res, message="Fuel Entry submitted successfully.")


@api_endpoint(allow_guest=False)
def calculate_fuel_average_api(assignment: str, odometer: float, fuel_qty: float) -> Dict[str, Any]:
	"""Calculates fuel average without saving — resolves vehicle from assignment."""
	vehicle_id = frappe.db.get_value("Vehicle Assignment", assignment, "vehicle") if frappe.db.exists("Vehicle Assignment", assignment) else None
	if not vehicle_id:
		return success_response(data={}, message="Cannot resolve vehicle from assignment.")
	stats = FuelAverageService.calculate_entry_average(vehicle_id, odometer, fuel_qty)
	return success_response(data=stats, message="Fuel average calculated successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_fuel_history_api(vehicle: str, limit: int = 20) -> Dict[str, Any]:
	"""Vehicle fuel history."""
	history = fuel_service.get_vehicle_history(vehicle, limit=limit)
	return success_response(data=history, message="Vehicle fuel history retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_employee_fuel_history_api(employee: str, limit: int = 20) -> Dict[str, Any]:
	"""Employee fuel history via assignment join."""
	history = fuel_service.get_employee_history(employee, limit=limit)
	return success_response(data=history, message="Employee fuel history retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_previous_odometer_api(vehicle: str, exclude_entry: str | None = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning the previous odometer reading for a vehicle."""
	if not frappe.db.exists("Vehicle", vehicle):
		return success_response(data={"previous_odometer": 0.0})

	filters = {"vehicle": vehicle, "docstatus": 1}
	if exclude_entry:
		filters["name"] = ["!=", exclude_entry]

	latest_fuel_odo = frappe.db.get_value("Fuel Entry", filters=filters, fieldname="MAX(odometer)") or 0.0
	odo = float(latest_fuel_odo)
	if not odo:
		odo = float(frappe.db.get_value("Vehicle", vehicle, "initial_odometer") or 0.0)

	return success_response(data={"previous_odometer": odo})
