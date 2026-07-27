"""
Vehicle Domain Service Architecture
Fleet Management System
"""

from typing import Any, Dict, List

import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.events.vehicle_events import VehicleEventDispatcher
from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetNotFoundError
from fleet_management.utils.logger import get_logger
from fleet_management.validators.vehicle_validator import VehicleValidator

logger = get_logger("fleet_management.services.vehicle")


class VehicleService(BaseService):
	"""
	Enterprise service managing business operations for Vehicle records and Digital Assets.
	Acts as the Single Source of Truth for Vehicle Status Mutations.
	"""

	def create_vehicle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new vehicle record."""
		return self.register_vehicle(payload)

	def register_vehicle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Registers a new Vehicle using minimal Category A inputs.
		Enforces registration policy in under 2 minutes.
		"""
		logger.info("Registering new vehicle via VehicleService", {"vehicle_number": payload.get("vehicle_number")})
		doc = frappe.get_doc({
			"doctype": "Vehicle",
			**payload
		})
		doc.insert()
		VehicleEventDispatcher.notify_vehicle_created(doc)
		return doc.as_dict()

	def update_vehicle(self, vehicle_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
		"""Updates vehicle parameters through service boundary."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")
		doc = frappe.get_doc("Vehicle", vehicle_id)
		doc.update(updates)
		doc.save()
		VehicleEventDispatcher.notify_vehicle_updated(doc)
		return doc.as_dict()

	def change_status(
		self,
		vehicle_id: str,
		new_status: str,
		reason: str | None = None,
		user: str | None = None
	) -> bool:
		"""
		Single Source of Truth method for changing vehicle status.
		Enforces state machine transitions, event dispatching, and audit logging.
		"""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		doc = frappe.get_doc("Vehicle", vehicle_id)
		old_status = doc.status

		if old_status == new_status:
			return True

		# Validate state machine transition
		validator = VehicleValidator({
			"license_plate": doc.registration_number or doc.vehicle_number,
			"vehicle_brand": doc.vehicle_brand,
			"vehicle_model": doc.vehicle_model,
			"vehicle_category": doc.vehicle_category,
			"company": doc.company,
			"current_status": old_status,
			"target_status": new_status
		})
		validator.raise_if_invalid()

		# Perform mutation bypass read-only check safely inside service
		frappe.db.set_value("Vehicle", vehicle_id, "status", new_status)
		doc.status = new_status

		logger.info(
			f"Status Changed: {vehicle_id} [{old_status} -> {new_status}]",
			{"reason": reason, "user": user or (frappe.session.user if hasattr(frappe, "session") else "System")}
		)

		VehicleEventDispatcher.notify_status_changed(doc, old_status, new_status)
		return True

	def update_status(self, vehicle_id: str, new_status: str) -> bool:
		"""Alias method delegating to change_status."""
		return self.change_status(vehicle_id, new_status)

	def activate_vehicle(self, vehicle_id: str) -> bool:
		"""Activates an inactive or draft vehicle."""
		res = self.change_status(vehicle_id, VehicleStatus.AVAILABLE, reason="Activated via VehicleService")
		if res and frappe.db.exists("Vehicle", vehicle_id):
			doc = frappe.get_doc("Vehicle", vehicle_id)
			VehicleEventDispatcher.notify_vehicle_created(doc)
		return res

	def deactivate_vehicle(self, vehicle_id: str, reason: str | None = None) -> bool:
		"""Deactivates an active vehicle."""
		res = self.change_status(vehicle_id, VehicleStatus.INACTIVE, reason=reason or "Deactivated via VehicleService")
		if res and frappe.db.exists("Vehicle", vehicle_id):
			doc = frappe.get_doc("Vehicle", vehicle_id)
			VehicleEventDispatcher.notify_vehicle_deactivated(doc)
		return res

	def archive_vehicle(self, vehicle_id: str) -> bool:
		"""Archives a vehicle."""
		res = self.change_status(vehicle_id, VehicleStatus.ARCHIVED, reason="Archived via VehicleService")
		if res and frappe.db.exists("Vehicle", vehicle_id):
			doc = frappe.get_doc("Vehicle", vehicle_id)
			VehicleEventDispatcher.notify_vehicle_archived(doc)
		return res

	def restore_vehicle(self, vehicle_id: str) -> bool:
		"""Restores an archived vehicle to Inactive."""
		return self.change_status(vehicle_id, VehicleStatus.INACTIVE, reason="Restored via VehicleService")

	def get_dashboard_summary(self, company: str | None = None) -> Dict[str, Any]:
		"""
		Returns aggregated vehicle metric counts for executive dashboard.
		Optimized query avoiding N+1 lookups.
		"""
		filters = {}
		if company:
			filters["company"] = company

		all_vehicles = frappe.get_all("Vehicle", filters=filters, fields=["name", "status"])

		counts = {
			"total_vehicles": len(all_vehicles),
			"available_count": sum(1 for v in all_vehicles if v.status == VehicleStatus.AVAILABLE),
			"assigned_count": sum(1 for v in all_vehicles if v.status == VehicleStatus.ASSIGNED),
			"maintenance_count": sum(1 for v in all_vehicles if v.status in (VehicleStatus.MAINTENANCE_DUE, VehicleStatus.UNDER_MAINTENANCE)),
			"out_of_service_count": sum(1 for v in all_vehicles if v.status == VehicleStatus.OUT_OF_SERVICE),
			"inactive_count": sum(1 for v in all_vehicles if v.status in (VehicleStatus.INACTIVE, VehicleStatus.ARCHIVED))
		}
		return counts

	def get_vehicle_summary(self, vehicle_id: str) -> Dict[str, Any]:
		"""Retrieves aggregated summary for target vehicle."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		sync_vehicle_operational_summary(vehicle_id)
		doc = frappe.get_doc("Vehicle", vehicle_id)
		asset_counts = self.get_asset_counts(vehicle_id)
		return {
			"vehicle_id": doc.name,
			"vehicle_number": doc.vehicle_number,
			"vehicle_name": doc.vehicle_name,
			"brand": doc.vehicle_brand,
			"model": doc.vehicle_model,
			"company": doc.company,
			"status": doc.status,
			"current_employee": doc.current_employee,
			"current_assignment_status": doc.current_assignment_status,
			"current_odometer": doc.current_odometer,
			"next_maintenance_due_odometer": doc.next_maintenance_due_odometer,
			"last_fuel_date": str(doc.last_fuel_date) if doc.last_fuel_date else None,
			"last_maintenance_date": str(doc.last_maintenance_date) if doc.last_maintenance_date else None,
			"average_fuel_economy": doc.average_fuel_economy,
			"total_fuel_cost": doc.total_fuel_cost,
			"total_maintenance_cost": doc.total_maintenance_cost,
			"lifetime_distance": doc.lifetime_distance,
			"document_count": asset_counts.get("document_count", 0),
			"image_count": asset_counts.get("image_count", 0),
			"primary_image": self.get_primary_image(vehicle_id)
		}

	def list_vehicles(
		self,
		filters: Dict[str, Any] | None = None,
		start: int = 0,
		page_length: int = 20
	) -> List[Dict[str, Any]]:
		"""Returns list of vehicles filtered by query criteria."""
		return frappe.get_list(
			"Vehicle",
			filters=filters or {},
			fields=[
				"name", "vehicle_number", "vehicle_name", "vehicle_brand",
				"vehicle_model", "company", "status", "current_odometer",
				"current_employee", "next_maintenance_due_odometer"
			],
			start=start,
			page_length=page_length,
			order_by="modified desc"
		)

	def get_vehicle_timeline(self, vehicle_id: str, limit: int = 50) -> List[Dict[str, Any]]:
		"""Retrieves chronological vehicle event history."""
		return frappe.get_all(
			"Activity Log",
			filters={"reference_doctype": "Vehicle", "reference_name": vehicle_id},
			fields=["name", "user", "subject", "creation"],
			order_by="creation desc",
			limit=limit
		)

	# --- Subsystem Integration Preparation Hooks ---

	def prepare_assignment(self, vehicle_id: str) -> Dict[str, Any]:
		"""Preparation contract hook for Vehicle Assignment module."""
		doc = frappe.get_doc("Vehicle", vehicle_id)
		return {"vehicle_id": vehicle_id, "can_assign": doc.status == VehicleStatus.AVAILABLE}

	def prepare_fuel(self, vehicle_id: str) -> Dict[str, Any]:
		"""Preparation contract hook for Fuel Entry module."""
		doc = frappe.get_doc("Vehicle", vehicle_id)
		return {"vehicle_id": vehicle_id, "can_fuel": doc.status != VehicleStatus.UNDER_MAINTENANCE}

	def prepare_maintenance(self, vehicle_id: str) -> Dict[str, Any]:
		"""Preparation contract hook for Maintenance module."""
		doc = frappe.get_doc("Vehicle", vehicle_id)
		return {"vehicle_id": vehicle_id, "current_odometer": doc.current_odometer}

	# --- Digital Asset Management Methods ---

	def get_asset_counts(self, vehicle_id: str) -> Dict[str, int]:
		"""Returns document and image counts for a vehicle."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			return {"document_count": 0, "image_count": 0}
		doc = frappe.get_doc("Vehicle", vehicle_id)
		return {
			"document_count": len(getattr(doc, "documents", []) or []),
			"image_count": len(getattr(doc, "images", []) or [])
		}

	def get_primary_image(self, vehicle_id: str) -> str | None:
		"""Retrieves primary image URL for vehicle gallery."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			return None
		doc = frappe.get_doc("Vehicle", vehicle_id)
		for img in (getattr(doc, "images", []) or []):
			if getattr(img, "is_primary", 0):
				return getattr(img, "image", None)
		if getattr(doc, "images", []):
			return getattr(doc.images[0], "image", None)
		return None

	def get_document_summary(self, vehicle_id: str) -> List[Dict[str, Any]]:
		"""Returns structured list of documents for a vehicle."""
		if not frappe.db.exists("Vehicle", vehicle_id):
			return []
		doc = frappe.get_doc("Vehicle", vehicle_id)
		result = []
		for d in (getattr(doc, "documents", []) or []):
			result.append({
				"document_type": d.document_type,
				"document_number": d.document_number,
				"issue_date": str(d.issue_date) if d.issue_date else None,
				"expiry_date": str(d.expiry_date) if d.expiry_date else None,
				"status": d.status,
				"attachment": d.attachment
			})
		return result

	def get_upcoming_expiries(self, within_days: int = 30) -> List[Dict[str, Any]]:
		"""Returns list of vehicle documents expiring within target days boundary."""
		return []


def sync_vehicle_operational_summary(vehicle_id: str):
	"""
	Central Operational Summary Synchronization Engine.
	Recalculates and saves Operational Summary fields on target Vehicle DB doc.
	"""
	if not hasattr(frappe, "db") or not vehicle_id or not frappe.db.exists("Vehicle", vehicle_id):
		return

	doc = frappe.get_doc("Vehicle", vehicle_id)
	doc.sync_operational_summary()

	update_dict = {
		"current_odometer": doc.current_odometer,
		"last_fuel_date": doc.last_fuel_date,
		"average_fuel_economy": doc.average_fuel_economy,
		"total_fuel_cost": doc.total_fuel_cost,
		"last_maintenance_date": doc.last_maintenance_date,
		"total_maintenance_cost": doc.total_maintenance_cost,
		"lifetime_distance": doc.lifetime_distance,
		"next_maintenance_due_odometer": doc.next_maintenance_due_odometer
	}

	if hasattr(frappe, "get_meta") and frappe.get_meta("Vehicle").has_field("last_maintenance_odometer"):
		update_dict["last_maintenance_odometer"] = getattr(doc, "last_maintenance_odometer", 0.0)

	frappe.db.set_value("Vehicle", doc.name, update_dict)
	frappe.db.commit()


def sync_all_vehicles_operational_summary():
	"""One-time or batch sync method across all vehicles in system."""
	if not hasattr(frappe, "get_all"):
		return
	vehicles = frappe.get_all("Vehicle", fields=["name"])
	for v in vehicles:
		sync_vehicle_operational_summary(v.name)


def is_vehicle_assigned(vehicle_id: str) -> bool:
	"""
	Determines whether a vehicle is currently assigned to an employee or has an active Vehicle Assignment record.
	"""
	if not vehicle_id or not hasattr(frappe, "db") or not frappe.db.exists("Vehicle", vehicle_id):
		return False

	current_employee = frappe.db.get_value("Vehicle", vehicle_id, "current_employee")
	if current_employee:
		return True

	current_assignment_status = frappe.db.get_value("Vehicle", vehicle_id, "current_assignment_status")
	if current_assignment_status == "Assigned":
		return True

	active_assignment = frappe.db.exists(
		"Vehicle Assignment",
		{
			"vehicle": vehicle_id,
			"status": ["in", ["Assigned", "In Use", "Approved"]],
		},
	)
	if active_assignment:
		return True

	return False


def update_vehicle_status_on_maintenance_change(doc, method=None):
	"""
	Automatically updates vehicle status based on Maintenance Work Order lifecycle:
	- When Work Order is created / active: changes vehicle status to 'Under Maintenance'.
	- When Work Order is completed (done) against 'Under Maintenance' or 'Maintenance Due':
	  - If vehicle is assigned to someone -> status becomes 'Assigned'
	  - If vehicle is not assigned -> status becomes 'Available'
	- When Work Order is cancelled while vehicle is 'Under Maintenance':
	  - Restores status to 'Assigned' (if assigned) or 'Available' (if unassigned).
	"""
	if not getattr(doc, "vehicle", None) or not hasattr(frappe, "db") or not frappe.db.exists("Vehicle", doc.vehicle):
		return

	vehicle_id = doc.vehicle
	current_v_status = frappe.db.get_value("Vehicle", vehicle_id, "status")
	wo_status = getattr(doc, "status", None)
	from fleet_management.enums import MaintenanceStatus, VehicleStatus

	svc = VehicleService()

	if wo_status == MaintenanceStatus.COMPLETED or wo_status == "Completed":
		if current_v_status in (VehicleStatus.UNDER_MAINTENANCE, VehicleStatus.MAINTENANCE_DUE):
			assigned = is_vehicle_assigned(vehicle_id)
			target_status = VehicleStatus.ASSIGNED if assigned else VehicleStatus.AVAILABLE
			target_assignment_status = "Assigned" if assigned else "Unassigned"
			svc.change_status(vehicle_id, target_status, reason=f"Maintenance Work Order '{doc.name}' completed")
			frappe.db.set_value("Vehicle", vehicle_id, "current_assignment_status", target_assignment_status)

	elif wo_status == MaintenanceStatus.CANCELLED or wo_status == "Cancelled":
		if current_v_status == VehicleStatus.UNDER_MAINTENANCE:
			assigned = is_vehicle_assigned(vehicle_id)
			target_status = VehicleStatus.ASSIGNED if assigned else VehicleStatus.AVAILABLE
			target_assignment_status = "Assigned" if assigned else "Unassigned"
			svc.change_status(vehicle_id, target_status, reason=f"Maintenance Work Order '{doc.name}' cancelled")
			frappe.db.set_value("Vehicle", vehicle_id, "current_assignment_status", target_assignment_status)

	else:
		# Created / Draft / Scheduled / In Progress / Open Work Order
		if current_v_status not in (
			VehicleStatus.UNDER_MAINTENANCE,
			VehicleStatus.INACTIVE,
			VehicleStatus.ARCHIVED,
			VehicleStatus.SOLD,
			VehicleStatus.SCRAPPED,
		):
			svc.change_status(vehicle_id, VehicleStatus.UNDER_MAINTENANCE, reason=f"Maintenance Work Order '{doc.name}' created/active")


# Document Event Handlers called by Frappe Hooks
def on_fuel_entry_change(doc, method=None):
	if getattr(doc, "vehicle", None):
		sync_vehicle_operational_summary(doc.vehicle)


def on_maint_order_change(doc, method=None):
	if getattr(doc, "vehicle", None):
		sync_vehicle_operational_summary(doc.vehicle)
		update_vehicle_status_on_maintenance_change(doc, method=method)


def on_maint_request_change(doc, method=None):
	if getattr(doc, "vehicle", None):
		sync_vehicle_operational_summary(doc.vehicle)


def on_assignment_change(doc, method=None):
	if getattr(doc, "vehicle", None):
		sync_vehicle_operational_summary(doc.vehicle)

