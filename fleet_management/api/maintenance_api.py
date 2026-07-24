"""
Maintenance Domain Whitelisted API Endpoints Implementation
Fleet Management System
"""

from typing import Any, Dict, Optional
import frappe
from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response, paginated_response
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.maintenance_due_service import MaintenanceDueEngine

maintenance_service = MaintenanceService()


@api_endpoint(allow_guest=False)
def search_maintenance_requests(
	vehicle: Optional[str] = None,
	status: Optional[str] = None,
	priority: Optional[str] = None,
	company: Optional[str] = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for searching maintenance requests."""
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if status:
		filters["status"] = status
	if priority:
		filters["priority"] = priority
	if company:
		filters["company"] = company

	start = (page - 1) * page_length
	items = frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=["name", "vehicle", "vehicle_number", "maintenance_type", "priority", "status", "requested_date", "company"],
		start=start,
		page_length=page_length,
		order_by="modified desc"
	)
	total_count = frappe.db.count("Maintenance Request", filters=filters) if hasattr(frappe, "db") else len(items)

	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def search_maintenance_orders(
	vehicle: Optional[str] = None,
	status: Optional[str] = None,
	workshop: Optional[str] = None,
	company: Optional[str] = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for searching maintenance work orders."""
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if status:
		filters["status"] = status
	if workshop:
		filters["workshop"] = workshop
	if company:
		filters["company"] = company

	start = (page - 1) * page_length
	items = frappe.get_list(
		"Maintenance Work Order",
		filters=filters,
		fields=["name", "maintenance_request", "vehicle", "assigned_technician", "workshop", "status", "start_date", "completion_date", "completion_odometer", "total_cost", "company"],
		start=start,
		page_length=page_length,
		order_by="modified desc"
	)
	total_count = frappe.db.count("Maintenance Work Order", filters=filters) if hasattr(frappe, "db") else len(items)

	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def create_maintenance_request_api(
	vehicle: str,
	maintenance_type: str,
	company: str,
	priority: str = "Medium",
	requested_date: Optional[str] = None,
	description: Optional[str] = None,
	workshop_name: Optional[str] = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for creating a maintenance request."""
	payload = {
		"vehicle": vehicle,
		"maintenance_type": maintenance_type,
		"company": company,
		"priority": priority,
		"requested_date": requested_date,
		"description": description,
		"workshop_name": workshop_name
	}
	res = maintenance_service.create_request(payload)
	return success_response(data=res, message="Maintenance Request created successfully.")


@api_endpoint(allow_guest=False)
def complete_work_order_api(
	work_order_id: str,
	completion_odometer: float,
	labour_cost: float = 0.0,
	parts_cost: float = 0.0,
	external_cost: float = 0.0,
	tax_amount: float = 0.0,
	discount_amount: float = 0.0
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for completing a maintenance work order & removing Maintenance Lock."""
	costs = {
		"labour_cost": labour_cost,
		"parts_cost": parts_cost,
		"external_cost": external_cost,
		"tax_amount": tax_amount,
		"discount_amount": discount_amount
	}
	res = maintenance_service.complete_work_order(work_order_id, completion_odometer, costs)
	return success_response(data=res, message="Maintenance Work Order completed successfully. Maintenance Lock removed.")


@api_endpoint(allow_guest=False)
def calculate_next_due_api(vehicle: str, completion_odometer: Optional[float] = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for calculating next due thresholds."""
	due_odo = MaintenanceDueEngine.calculate_next_due_odometer(vehicle, completion_odometer)
	due_date = MaintenanceDueEngine.calculate_next_due_date(vehicle)
	return success_response(data={"vehicle": vehicle, "next_due_odometer": due_odo, "next_due_date": due_date}, message="Next due thresholds calculated.")


@api_endpoint(allow_guest=False)
def get_maintenance_summary(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving vehicle maintenance summary statistics."""
	summary = maintenance_service.get_summary(vehicle)
	return success_response(data=summary, message="Maintenance summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_upcoming_maintenance_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving upcoming maintenance schedule."""
	schedule = MaintenanceDueEngine.get_upcoming_maintenance_schedule(vehicle)
	return success_response(data=schedule, message="Upcoming maintenance schedule retrieved.")
