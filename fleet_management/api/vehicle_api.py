"""
Vehicle Domain Whitelisted API Endpoints Implementation
Fleet Management System
"""

from typing import Any, Dict, List, Optional
import frappe
from fleet_management.api.base import api_endpoint
from fleet_management.api.responses import success_response, paginated_response
from fleet_management.services.vehicle_service import VehicleService

vehicle_service = VehicleService()


@api_endpoint(allow_guest=False)
def search_vehicles(
	query: Optional[str] = None,
	brand: Optional[str] = None,
	status: Optional[str] = None,
	company: Optional[str] = None,
	page: int = 1,
	page_length: int = 20
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for searching vehicles."""
	filters = {}
	if brand:
		filters["vehicle_brand"] = brand
	if status:
		filters["status"] = status
	if company:
		filters["company"] = company
	if query:
		filters["vehicle_number"] = ["like", f"%{query}%"]

	start = (page - 1) * page_length
	items = vehicle_service.list_vehicles(filters=filters, start=start, page_length=page_length)
	total_count = frappe.db.count("Vehicle", filters=filters) if hasattr(frappe, "db") else len(items)

	return paginated_response(items=items, total_count=total_count, page=page, page_length=page_length)


@api_endpoint(allow_guest=False)
def get_vehicle_summary(vehicle_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint retrieving aggregated vehicle summary."""
	summary = vehicle_service.get_vehicle_summary(vehicle_id)
	return success_response(data=summary, message="Vehicle summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def create_vehicle(
	vehicle_number: str,
	vehicle_brand: str,
	vehicle_model: str,
	vehicle_category: str,
	company: str,
	registration_number: Optional[str] = None,
	initial_odometer: float = 0.0
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for registering a vehicle using Category A minimal payload."""
	payload = {
		"vehicle_number": vehicle_number,
		"vehicle_brand": vehicle_brand,
		"vehicle_model": vehicle_model,
		"vehicle_category": vehicle_category,
		"company": company,
		"registration_number": registration_number,
		"initial_odometer": initial_odometer
	}
	res = vehicle_service.register_vehicle(payload)
	return success_response(data=res, message="Vehicle registered successfully.")


@api_endpoint(allow_guest=False)
def change_vehicle_status(
	vehicle_id: str,
	new_status: str,
	reason: Optional[str] = None
) -> Dict[str, Any]:
	"""Whitelisted API endpoint for single-source-of-truth status mutation."""
	res = vehicle_service.change_status(vehicle_id, new_status, reason=reason)
	return success_response(data={"updated": res, "status": new_status}, message="Vehicle status changed successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_dashboard_summary(company: Optional[str] = None) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning executive dashboard metrics."""
	data = vehicle_service.get_dashboard_summary(company=company)
	return success_response(data=data, message="Dashboard summary retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_timeline_api(vehicle_id: str, limit: int = 50) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning vehicle activity timeline."""
	timeline = vehicle_service.get_vehicle_timeline(vehicle_id, limit=limit)
	return success_response(data=timeline, message="Vehicle timeline retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_quick_actions(vehicle_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning available quick actions."""
	actions = [
		{"action": "assign", "label": "Assign Vehicle"},
		{"action": "fuel", "label": "Record Fuel"},
		{"action": "maintenance", "label": "Record Maintenance"},
		{"action": "change_status", "label": "Change Status"},
		{"action": "timeline", "label": "View Timeline"}
	]
	return success_response(data={"vehicle_id": vehicle_id, "actions": actions}, message="Quick actions retrieved.")


@api_endpoint(allow_guest=False)
def get_vehicle_documents(vehicle_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning vehicle document attachments."""
	docs = vehicle_service.get_document_summary(vehicle_id)
	return success_response(data=docs, message="Vehicle documents retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_images(vehicle_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning vehicle image gallery."""
	if not frappe.db.exists("Vehicle", vehicle_id):
		return success_response(data=[], message="Vehicle not found.")
	doc = frappe.get_doc("Vehicle", vehicle_id)
	images = [img.as_dict() for img in (getattr(doc, "images", []) or [])]
	return success_response(data=images, message="Vehicle images retrieved successfully.")


@api_endpoint(allow_guest=False)
def get_vehicle_asset_summary(vehicle_id: str) -> Dict[str, Any]:
	"""Whitelisted API endpoint returning combined document & image summary."""
	counts = vehicle_service.get_asset_counts(vehicle_id)
	primary_image = vehicle_service.get_primary_image(vehicle_id)
	data = {
		"vehicle_id": vehicle_id,
		"document_count": counts.get("document_count", 0),
		"image_count": counts.get("image_count", 0),
		"primary_image": primary_image
	}
	return success_response(data=data, message="Asset summary retrieved successfully.")
