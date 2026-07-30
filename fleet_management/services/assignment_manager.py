"""
Assignment Manager Service
Fleet Management System (Frappe v15)

Responsible for vehicle assignment lifecycle, availability validation,
concurrency locking, return management, and triggering VehicleStateManager.
"""

from typing import Any, Dict, List, Optional
import frappe

from fleet_management.business_rules.assignment_rules import (
	AssignmentActiveDuplicateRule,
	AssignmentOdometerIntegrityRule,
	AssignmentVehicleAvailabilityRule,
)
from fleet_management.enums import AssignmentStatus, VehicleStatus
from fleet_management.events.assignment_events import AssignmentEventDispatcher
from fleet_management.services.base_service import BaseService
from fleet_management.services.vehicle_state_manager import VehicleStateManager
from fleet_management.utils.exceptions import FleetNotFoundError, FleetValidationError
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.assignment_manager")


class AssignmentManager(BaseService):
	"""
	Enterprise manager for Vehicle Assignment transactions.
	Delegates status mutations to VehicleStateManager.
	"""

	def __init__(self):
		super().__init__()
		self.state_manager = VehicleStateManager()

	def validate_vehicle_availability(self, vehicle_id: str) -> bool:
		"""
		Checks that a vehicle is currently available for assignment.
		Enforces ASSIGN-001 rule.
		"""
		if not frappe.db.exists("Vehicle", vehicle_id):
			raise FleetNotFoundError(f"Vehicle '{vehicle_id}' not found.")

		v_status = frappe.db.get_value("Vehicle", vehicle_id, "status")
		if v_status != VehicleStatus.AVAILABLE:
			rule = AssignmentVehicleAvailabilityRule({"vehicle_status": v_status})
			rule.raise_if_violated()

		# Check active submitted assignments
		active_count = frappe.db.count(
			"Vehicle Assignment",
			filters={
				"vehicle": vehicle_id,
				"docstatus": 1,
				"return_date": ["is", "not set"],
				"status": ["in", [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_USE, AssignmentStatus.APPROVED, AssignmentStatus.RETURN_OVERDUE]],
			}
		) if hasattr(frappe, "db") else 0

		if active_count > 0:
			rule = AssignmentActiveDuplicateRule({"active_assignments_count": active_count})
			rule.raise_if_violated()

		return True

	def create_assignment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		"""Creates a new Vehicle Assignment document."""
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

	def assign_vehicle(
		self,
		assignment_id: str,
		opening_odometer: Optional[float] = None,
		handover_notes: Optional[str] = None
	) -> bool:
		"""
		Handover Workflow with DB Row Lock:
		Acquires atomic FOR UPDATE lock on Vehicle, validates availability, sets assignment status,
		and delegates state update to VehicleStateManager.
		"""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")

		doc = frappe.get_doc("Vehicle Assignment", assignment_id)

		# 1. Acquire DB Concurrency Lock on Vehicle
		frappe.db.sql("SELECT name FROM `tabVehicle` WHERE name=%s FOR UPDATE", (doc.vehicle,))

		# 2. Validate Vehicle Availability
		self.validate_vehicle_availability(doc.vehicle)

		# 3. Odometer Verification — use initial_odometer as baseline
		v_odo = float(frappe.db.get_value("Vehicle", doc.vehicle, "initial_odometer") or 0.0)
		if opening_odometer is not None:
			odometer_rule = AssignmentOdometerIntegrityRule({
				"opening_odometer": opening_odometer,
				"current_vehicle_odometer": v_odo
			})
			odometer_rule.raise_if_violated()
			doc.opening_odometer = float(opening_odometer)
		elif not doc.opening_odometer:
			doc.opening_odometer = v_odo

		if handover_notes:
			doc.handover_notes = handover_notes

		doc.status = AssignmentStatus.ASSIGNED

		# Submit if draft
		if doc.docstatus == 0:
			doc.submit()
		else:
			doc.save()

		# 4. Recalculate Vehicle State via VehicleStateManager
		self.state_manager.update_vehicle_state(doc.vehicle, reason=f"Handover via Assignment {assignment_id}")

		AssignmentEventDispatcher.notify_handover(doc)
		logger.info(f"Vehicle Handover completed for assignment: {assignment_id}")
		return True

	def return_vehicle(
		self,
		assignment_id: str,
		closing_odometer: float,
		return_notes: Optional[str] = None,
		return_condition: Optional[str] = None
	) -> bool:
		"""
		Return Workflow:
		Validates closing odometer, records return timestamp, clears current_employee,
		and delegates state recalculation to VehicleStateManager.
		"""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")

		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		opening = float(doc.opening_odometer or 0.0)
		closing = float(closing_odometer)

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

		# Recalculate Vehicle State
		self.state_manager.update_vehicle_state(doc.vehicle, reason=f"Vehicle returned via Assignment {assignment_id}")

		AssignmentEventDispatcher.notify_returned(doc)
		logger.info(f"Vehicle Returned for assignment: {assignment_id}, Distance: {doc.distance_travelled} KM")
		return True

	def cancel_assignment(self, assignment_id: str, reason: Optional[str] = None) -> bool:
		"""
		Transaction Reversal for Assignment:
		Cancels assignment, restores vehicle current_employee to None, and recalculates vehicle state.
		"""
		if not frappe.db.exists("Vehicle Assignment", assignment_id):
			raise FleetNotFoundError(f"Assignment '{assignment_id}' not found.")

		doc = frappe.get_doc("Vehicle Assignment", assignment_id)
		if doc.docstatus != 2:
			doc.status = AssignmentStatus.CANCELLED
			if doc.docstatus == 1:
				doc.cancel()
			else:
				doc.save()

		self.state_manager.update_vehicle_state(doc.vehicle, reason=reason or f"Assignment {assignment_id} cancelled")

		AssignmentEventDispatcher.notify_cancelled(doc)
		logger.info(f"Cancelled assignment: {assignment_id}")
		return True
