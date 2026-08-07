"""
Assignment Domain Whitelisted API Endpoints Implementation
Fleet Management System
"""

from typing import Any, Dict

import frappe

from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import paginated_response, success_response
from fleet_management.services.assignment_service import AssignmentService

assignment_service = AssignmentService()


@api_endpoint(allow_guest=False)
def search_assignments(
	vehicle: str | None = None,
	employee: str | None = None,
	status: str | None = None,
	company: str | None = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for searching vehicle assignments."""
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if employee:
		filters["employee"] = employee
	if status:
		filters["status"] = status
	if company:
		filters["company"] = company

	start = (page - 1) * page_length
	items = frappe.get_list(
		"Vehicle Assignment",
		filters=filters,
		fields=["name", "vehicle", "vehicle_name", "employee", "employee_name", "company", "status", "assignment_date", "expected_return_date"],
		start=start,
		page_length=page_length,
		order_by="modified desc"
	)
	total_count = frappe.db.count("Vehicle Assignment", filters=filters) if hasattr(frappe, "db") else len(items)

	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def get_assignment_summary(assignment_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving aggregated assignment summary."""
	summary = assignment_service.get_assignment_summary(assignment_id)
	return success_response(data=summary, message="Assignment summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def create_assignment(
	vehicle: str,
	employee: str,
	company: str,
	assignment_date: str | None = None,
	expected_return_date: str | None = None,
	purpose: str | None = None,
	opening_odometer: float | None = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for creating a vehicle assignment using minimal payload."""
	payload = {
		"vehicle": vehicle,
		"employee": employee,
		"company": company,
		"assignment_date": assignment_date,
		"expected_return_date": expected_return_date,
		"purpose": purpose,
		"opening_odometer": opening_odometer
	}
	res = assignment_service.create_assignment(payload)
	return success_response(data=res, message="Vehicle Assignment created successfully.")


@api_endpoint(allow_guest=False)
def assign_vehicle_api(
	assignment_id: str,
	opening_odometer: float | None = None,
	handover_notes: str | None = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for executing Vehicle Handover."""
	res = assignment_service.assign_vehicle(
		assignment_id,
		opening_odometer=opening_odometer,
		handover_notes=handover_notes
	)
	return success_response(data={"success": res}, message="Vehicle Handover completed successfully.")


@api_endpoint(allow_guest=False)
def return_vehicle_api(
	assignment_id: str,
	closing_odometer: float,
	return_date: str | None = None,
	return_notes: str | None = None,
	return_condition: str | None = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for executing Vehicle Return."""
	res = assignment_service.return_vehicle(
		assignment_id,
		closing_odometer=closing_odometer,
		return_date=return_date,
		return_notes=return_notes,
		return_condition=return_condition
	)
	return success_response(data={"success": res}, message="Vehicle Returned successfully.")


@api_endpoint(allow_guest=False)
def close_assignment_api(assignment_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for closing an assignment."""
	res = assignment_service.close_assignment(assignment_id)
	return success_response(data={"success": res}, message="Assignment Closed successfully.")


@api_endpoint(allow_guest=False)
def cancel_assignment_api(assignment_id: str, reason: str | None = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for cancelling an assignment."""
	res = assignment_service.cancel_assignment(assignment_id, reason=reason)
	return success_response(data={"success": res}, message="Assignment Cancelled successfully.")


@api_endpoint(allow_guest=False)
def get_assignment_timeline_api(assignment_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving assignment timeline events."""
	if not frappe.db.exists("Vehicle Assignment", assignment_id):
		return success_response(data=[], message="Assignment not found.")
	timeline = frappe.get_all(
		"Activity Log",
		filters={"reference_doctype": "Vehicle Assignment", "reference_name": assignment_id},
		fields=["name", "user", "subject", "creation"],
		order_by="creation desc"
	)
	return success_response(data=timeline, message="Assignment timeline retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_opening_odometer_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving latest fuel entry odometer or initial odometer for vehicle."""
	if not frappe.db.exists("Fleet Vehicle", vehicle):
		return success_response(data={"opening_odometer": 0.0, "company": None})

	company = frappe.db.get_value("Fleet Vehicle", vehicle, "company")
	latest_fuel_odo = frappe.db.get_value(
		"Fuel Entry",
		filters={"vehicle": vehicle, "docstatus": 1},
		fieldname="MAX(odometer)"
	) or 0.0

	odo = float(latest_fuel_odo)
	if not odo:
		odo = float(frappe.db.get_value("Fleet Vehicle", vehicle, "initial_odometer") or 0.0)

	return success_response(data={"opening_odometer": odo, "company": company})
