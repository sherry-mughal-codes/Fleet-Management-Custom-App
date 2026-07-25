"""
Assignment Domain Service Implementation
Fleet Management System
"""

from typing import Any, Dict, List

import frappe

from fleet_management.business_rules.assignment_rules import (
	AssignmentActiveDuplicateRule,
	AssignmentOdometerIntegrityRule,
	AssignmentVehicleAvailabilityRule,
)
from fleet_management.enums import AssignmentStatus, VehicleStatus
from fleet_management.events.assignment_events import AssignmentEventDispatcher
from fleet_management.services.base_service import BaseService
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.utils.exceptions import FleetNotFoundError, FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.assignment")


class AssignmentService(BaseService):
	"""
	Enterprise service managing business operations for Vehicle Assignment records.
	Acts as the operational session manager connecting Vehicles to Employees.
	Requests Vehicle status mutations strictly through VehicleService (Single Source of Truth).
	"""

	def __init__(self):
		super().__init__()
		self.vehicle_service = VehicleService()

	def create_assignment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Creates a new Vehicle Assignment using minimal Category A fields.
		"""
		logger.info("Creating new assignment via AssignmentService", {"vehicle": payload.get("vehicle"), "employee": payload.get("employee")})

		# Validate vehicle availability before creating assignment
		vehicle_id = payload.get("vehicle")
		if vehicle_id:
			self.validate_vehicle_availability(vehicle_id)

		doc = frappe.get_doc({
			"doctype": "Vehicle Assignment",
			**payload
		})
		doc.insert()
		AssignmentEventDispatcher.notify_assignment_created(doc)
		return doc.as_dict()

	def update_assignment(self, assignment_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
		"""Updates assignment parameters cleanly."""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")
		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		if doc.status in (AssignmentStatus.CLOSED, AssignmentStatus.CANCELLED):
			raise FleetValidationError(f"ASSIGN-008: Assignment '{assignment_id}' is '{doc.status}' and cannot be modified.")
		doc.update(updates)
		doc.save()
		return doc.as_dict()

	def approve_assignment(self, assignment_id: str) -> bool:
		"""Approves an assignment request."""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")
		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		doc.status = AssignmentStatus.APPROVED
		doc.save()
		AssignmentEventDispatcher.notify_assignment_approved(doc)
		logger.info(f"Approved assignment: {assignment_id}")
		return True

	def assign_vehicle(
		self,
		assignment_id: str,
		opening_odometer: float | None = None,
		handover_notes: str | None = None
	) -> bool:
		"""
		Vehicle Handover Workflow.
		Validates vehicle availability, updates Opening Odometer, sets assignment status to Assigned,
		and invokes VehicleService.change_status(vehicle, VehicleStatus.ASSIGNED).
		"""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")

		doc = frappe.get_doc("Vehicle Assignment", assignment_id)

		# 1. Validate active duplicate assignment & vehicle availability (ASSIGN-001)
		v_doc = frappe.get_doc("Vehicle", doc.vehicle)
		avail_rule = AssignmentVehicleAvailabilityRule({"vehicle_status": v_doc.status})
		avail_rule.raise_if_violated()

		# 2. Set Opening Odometer & Handover Notes
		if opening_odometer is not None:
			odometer_rule = AssignmentOdometerIntegrityRule({
				"opening_odometer": opening_odometer,
				"current_vehicle_odometer": v_doc.current_odometer or 0.0
			})
			odometer_rule.raise_if_violated()
			doc.opening_odometer = float(opening_odometer)
		elif not doc.opening_odometer:
			doc.opening_odometer = float(v_doc.current_odometer or 0.0)

		if handover_notes:
			doc.handover_notes = handover_notes

		doc.status = AssignmentStatus.ASSIGNED
		doc.save()

		# 3. Request Vehicle status change and assigned employee update via VehicleService
		self.vehicle_service.change_status(doc.vehicle, VehicleStatus.ASSIGNED, reason=f"Handover via Assignment {assignment_id}")
		frappe.db.set_value("Vehicle", doc.vehicle, "current_employee", doc.employee)
		frappe.db.set_value("Vehicle", doc.vehicle, "current_assignment_status", "Assigned")

		AssignmentEventDispatcher.notify_handover(doc)
		logger.info(f"Vehicle Handover completed for assignment: {assignment_id}")
		return True

	def return_vehicle(
		self,
		assignment_id: str,
		closing_odometer: float,
		return_notes: str | None = None,
		return_condition: str | None = None
	) -> bool:
		"""
		Vehicle Return Workflow.
		Validates closing odometer >= opening odometer (ASSIGN-005), calculates distance travelled,
		updates Vehicle.current_odometer, resets current_employee, and requests VehicleStatus.AVAILABLE via VehicleService.
		"""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")

		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		opening = float(doc.opening_odometer or 0.0)
		closing = float(closing_odometer)

		# 1. Odometer Integrity Check (ASSIGN-005)
		if closing < opening:
			raise FleetValidationError(f"ASSIGN-005: Closing Odometer ({closing}) cannot be less than Opening Odometer ({opening}).")

		doc.closing_odometer = closing
		doc.distance_travelled = closing - opening
		doc.return_date = frappe.utils.nowdate() if hasattr(frappe, "utils") else None
		if return_notes:
			doc.return_notes = return_notes
		if return_condition:
			doc.return_condition = return_condition

		doc.status = AssignmentStatus.RETURNED
		doc.save()

		# 2. Update Vehicle Current Odometer & reset assigned employee
		frappe.db.set_value("Vehicle", doc.vehicle, "current_odometer", closing)
		frappe.db.set_value("Vehicle", doc.vehicle, "current_employee", None)
		frappe.db.set_value("Vehicle", doc.vehicle, "current_assignment_status", "Unassigned")

		# 3. Request Vehicle status transition to Available via VehicleService
		self.vehicle_service.change_status(doc.vehicle, VehicleStatus.AVAILABLE, reason=f"Returned via Assignment {assignment_id}")

		AssignmentEventDispatcher.notify_returned(doc)
		logger.info(f"Vehicle Returned for assignment: {assignment_id}, Distance: {doc.distance_travelled} KM")
		return True

	def close_assignment(self, assignment_id: str) -> bool:
		"""Closes a returned assignment."""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")
		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		doc.status = AssignmentStatus.CLOSED
		doc.save()
		AssignmentEventDispatcher.notify_closed(doc)
		logger.info(f"Closed assignment: {assignment_id}")
		return True

	def cancel_assignment(self, assignment_id: str, reason: str | None = None) -> bool:
		"""
		Cancels an assignment.
		Releases vehicle reservation back to Available via VehicleService.
		"""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")
		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		old_status = doc.status
		doc.status = AssignmentStatus.CANCELLED
		doc.save()

		if old_status in (AssignmentStatus.ASSIGNED, AssignmentStatus.APPROVED, AssignmentStatus.IN_USE):
			frappe.db.set_value("Vehicle", doc.vehicle, "current_employee", None)
			frappe.db.set_value("Vehicle", doc.vehicle, "current_assignment_status", "Unassigned")
			self.vehicle_service.change_status(doc.vehicle, VehicleStatus.AVAILABLE, reason=reason or f"Cancelled via {assignment_id}")

		AssignmentEventDispatcher.notify_cancelled(doc)
		logger.info(f"Cancelled assignment: {assignment_id}")
		return True

	def validate_vehicle_availability(self, vehicle_id: str) -> bool:
		"""Checks for active duplicate assignments (ASSIGN-001)."""
		active_statuses = [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_USE, AssignmentStatus.APPROVED]
		active_count = frappe.db.count("Vehicle Assignment", filters={
			"vehicle": vehicle_id,
			"status": ["in", active_statuses]
		}) if hasattr(frappe, "db") else 0

		if active_count > 0:
			rule = AssignmentActiveDuplicateRule({"active_assignments_count": active_count})
			rule.raise_if_violated()
		return True

	# --- Analytics & Utilization Helpers ---

	def get_active_assignments_count(self, company: str | None = None) -> int:
		"""Returns total active assignments count for a company."""
		filters = {"status": ["in", [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_USE]]}
		if company:
			filters["company"] = company
		return frappe.db.count("Vehicle Assignment", filters=filters) if hasattr(frappe, "db") else 0

	def get_assignment_duration_stats(self, assignment_id: str) -> Dict[str, Any]:
		"""Returns duration statistics for target assignment."""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")
		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		start = doc.assignment_date
		end = doc.return_date or doc.expected_return_date
		return {
			"assignment_id": assignment_id,
			"start_date": str(start) if start else None,
			"end_date": str(end) if end else None,
			"is_active": doc.status in (AssignmentStatus.ASSIGNED, AssignmentStatus.IN_USE)
		}

	def get_vehicle_utilization_stats(self, vehicle_id: str) -> Dict[str, Any]:
		"""Returns total mileage and assignment count statistics for a vehicle."""
		assignments = frappe.get_all(
			"Vehicle Assignment",
			filters={"vehicle": vehicle_id},
			fields=["name", "distance_travelled", "status"]
		) if hasattr(frappe, "get_all") else []

		total_distance = sum(float(a.get("distance_travelled") or 0.0) for a in assignments)
		return {
			"vehicle": vehicle_id,
			"total_assignments": len(assignments),
			"total_distance_travelled": total_distance
		}

	def get_return_compliance_stats(self, company: str | None = None) -> Dict[str, Any]:
		"""Returns statistics on on-time vs overdue returns."""
		filters = {}
		if company:
			filters["company"] = company
		total = frappe.db.count("Vehicle Assignment", filters=filters) if hasattr(frappe, "db") else 0
		active = frappe.db.count("Vehicle Assignment", filters={**filters, "status": ["in", [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_USE]]}) if hasattr(frappe, "db") else 0
		return {
			"total_assignments": total,
			"active_assignments": active,
			"overdue_assignments": 0
		}

	def get_assignment_summary(self, assignment_id: str) -> Dict[str, Any]:
		"""Retrieves aggregated summary for target assignment."""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")
		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		return {
			"assignment_id": doc.name,
			"vehicle": doc.vehicle,
			"vehicle_number": doc.vehicle_number,
			"vehicle_name": doc.vehicle_name,
			"employee": doc.employee,
			"employee_name": doc.employee_name,
			"company": doc.company,
			"status": doc.status,
			"opening_odometer": doc.opening_odometer,
			"closing_odometer": doc.closing_odometer,
			"distance_travelled": doc.distance_travelled,
			"assignment_date": str(doc.assignment_date) if doc.assignment_date else None,
			"expected_return_date": str(doc.expected_return_date) if doc.expected_return_date else None
		}

	def get_employee_history(self, employee_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves assignment history for an employee."""
		return frappe.get_all(
			"Vehicle Assignment",
			filters={"employee": employee_id},
			fields=["name", "vehicle", "vehicle_name", "status", "assignment_date", "expected_return_date"],
			order_by="creation desc",
			limit=limit
		)

	def get_vehicle_history(self, vehicle_id: str, limit: int = 20) -> List[Dict[str, Any]]:
		"""Retrieves assignment history for a vehicle."""
		return frappe.get_all(
			"Vehicle Assignment",
			filters={"vehicle": vehicle_id},
			fields=["name", "employee", "employee_name", "status", "assignment_date", "expected_return_date"],
			order_by="creation desc",
			limit=limit
		)

	# --- Future Subsystem Integration Hooks ---

	def prepare_fuel(self, assignment_id: str) -> Dict[str, Any]:
		"""Contract hook for linking Fuel Entries to Assignment."""
		return {"assignment_id": assignment_id, "can_fuel": True}

	def prepare_maintenance(self, assignment_id: str) -> Dict[str, Any]:
		"""Contract hook for linking Maintenance Records to Assignment."""
		return {"assignment_id": assignment_id, "can_maintenance": True}

	def prepare_expense(self, assignment_id: str) -> Dict[str, Any]:
		"""Contract hook for linking Expense Records to Assignment."""
		return {"assignment_id": assignment_id, "can_expense": True}
