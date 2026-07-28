"""
Maintenance Domain Whitelisted API Endpoints Implementation
Fleet Management System (Frappe v15)
"""

from typing import Any, Dict

import frappe

from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import paginated_response, success_response
from fleet_management.services.maintenance_manager import MaintenanceManager

maintenance_manager = MaintenanceManager()


@api_endpoint(allow_guest=False)
def search_maintenance_entries(
	vehicle: str | None = None,
	assignment: str | None = None,
	maintenance_type: str | None = None,
	company: str | None = None,
	docstatus: int | None = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for searching Maintenance Entries."""
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if assignment:
		filters["assignment"] = assignment
	if maintenance_type:
		filters["maintenance_type"] = maintenance_type
	if company:
		filters["company"] = company
	if docstatus is not None:
		filters["docstatus"] = docstatus

	start = (page - 1) * page_length
	items = frappe.get_list(
		"Maintenance Entry",
		filters=filters,
		fields=["name", "assignment", "vehicle", "employee", "maintenance_date", "current_odometer", "maintenance_type", "rate", "qty", "total_cost", "docstatus", "company"],
		start=start,
		page_length=page_length,
		order_by="modified desc"
	) if hasattr(frappe, "get_list") else []

	total_count = frappe.db.count("Maintenance Entry", filters=filters) if hasattr(frappe, "db") else len(items)
	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def create_maintenance_entry_api(
	assignment: str,
	maintenance_type: str,
	rate: float,
	qty: float = 1.0,
	current_odometer: float | None = None,
	maintenance_date: str | None = None,
	vendor: str | None = None,
	invoice_number: str | None = None,
	remarks: str | None = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for creating a Maintenance Entry."""
	payload = {
		"assignment": assignment,
		"maintenance_type": maintenance_type,
		"rate": rate,
		"qty": qty,
		"current_odometer": current_odometer,
		"maintenance_date": maintenance_date,
		"vendor": vendor,
		"invoice_number": invoice_number,
		"remarks": remarks
	}
	res = maintenance_manager.create_maintenance_entry(payload)
	return success_response(data=res, message="Maintenance Entry created successfully.")


@api_endpoint(allow_guest=False)
def submit_maintenance_entry_api(entry_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for submitting a Maintenance Entry."""
	res = maintenance_manager.submit_maintenance_entry(entry_id)
	return success_response(data=res, message="Maintenance Entry submitted successfully.")


@api_endpoint(allow_guest=False)
def cancel_maintenance_entry_api(entry_id: str, reason: str | None = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint for cancelling a Maintenance Entry."""
	res = maintenance_manager.cancel_maintenance_entry(entry_id, reason=reason)
	return success_response(data={"cancelled": res}, message="Maintenance Entry cancelled successfully.")


@api_endpoint(allow_guest=False)
def get_due_maintenance_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving due maintenance schedule items."""
	due = maintenance_manager.get_due_maintenance(vehicle)
	return success_response(data=due, message="Due maintenance items retrieved.")


@api_endpoint(allow_guest=False)
def get_overdue_maintenance_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for retrieving overdue maintenance schedule items."""
	overdue = maintenance_manager.get_overdue_maintenance(vehicle)
	return success_response(data=overdue, message="Overdue maintenance items retrieved.")


@api_endpoint(allow_guest=False)
def get_vehicle_health_api(vehicle: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint for calculating vehicle operational health score."""
	health = maintenance_manager.get_vehicle_health(vehicle)
	return success_response(data=health, message="Vehicle health retrieved.")


@api_endpoint(allow_guest=False)
def get_due_maintenance_items_api(assignment: str, current_odometer: float | None = None) -> Dict[str, Any]:
	"""
	Resolves vehicle from assignment, evaluates template interval schedule lines
	against current_odometer, and returns items that are due or overdue.
	"""
	if not assignment or not hasattr(frappe, "db") or not frappe.db.exists("Vehicle Assignment", assignment):
		return success_response(data=[], message="Assignment not found.")

	v_id = frappe.db.get_value("Vehicle Assignment", assignment, "vehicle")
	if not v_id:
		return success_response(data=[], message="Vehicle not found.")

	odo = float(current_odometer) if current_odometer and float(current_odometer) > 0 else None
	due_items = maintenance_manager.get_due_maintenance(v_id)
	overdue_items = maintenance_manager.get_overdue_maintenance(v_id, current_odometer=odo)

	seen = set()
	items = []
	for item in (overdue_items + due_items):
		m_type = item.get("maintenance_type")
		if m_type and m_type not in seen:
			seen.add(m_type)
			items.append({
				"item_name": m_type,
				"interval_km": float(item.get("interval_km") or 0.0),
				"is_mandatory": 1 if item.get("is_mandatory") else 0,
				"priority": item.get("priority", "Medium"),
				"grace_distance": float(item.get("grace_distance") or 0.0),
				"description": f"Servicing due (exceeded by {item.get('exceeded_km', 0)} KM)" if item.get("exceeded_km") else "Routine Servicing Due",
				"is_completed": 1,
				"cost": 0.0
			})

	if not items:
		template_id = maintenance_manager.get_active_template(v_id)
		if template_id:
			lines = maintenance_manager.get_template_lines(template_id)
			for line in lines:
				m_type = getattr(line, "maintenance_type", None) or (line.get("maintenance_type") if isinstance(line, dict) else "")
				if m_type and m_type not in seen:
					seen.add(m_type)
					items.append({
						"item_name": m_type,
						"interval_km": float(getattr(line, "interval_km", 0.0) or 0.0),
						"is_mandatory": getattr(line, "is_mandatory", 0),
						"priority": getattr(line, "priority", "Medium"),
						"grace_distance": float(getattr(line, "grace_distance", 0.0) or 0.0),
						"description": getattr(line, "description", "") or "Routine Servicing",
						"is_completed": 1,
						"cost": 0.0
					})

	return success_response(data=items, message="Due maintenance items retrieved.")
