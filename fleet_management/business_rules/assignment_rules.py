"""
Assignment Business Invariant Rules Architecture
Fleet Management System
"""

from fleet_management.business_rules.base_rule import BaseBusinessRule
from fleet_management.enums import VehicleStatus, AssignmentStatus


class AssignmentVehicleAvailabilityRule(BaseBusinessRule):
	"""
	Rule ASSIGN-001: Verifies vehicle is Available before initiating assignment.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("vehicle_status")
		if vehicle_status != VehicleStatus.AVAILABLE:
			self.add_violation(f"ASSIGN-001: Cannot assign vehicle with status '{vehicle_status}'. Must be Available.")
			return False
		return True


class AssignmentActiveDuplicateRule(BaseBusinessRule):
	"""
	Rule ASSIGN-001: Prevents duplicate active assignments for the same vehicle.
	"""

	def evaluate(self) -> bool:
		active_count = self.context.get("active_assignments_count", 0)
		if active_count > 0:
			self.add_violation("ASSIGN-001: Vehicle currently has an active assignment in progress.")
			return False
		return True


class AssignmentOdometerIntegrityRule(BaseBusinessRule):
	"""
	Rule ASSIGN-004 & ASSIGN-005: Validates opening and closing odometer readings.
	Never allows closing odometer to decrease vehicle mileage.
	"""

	def evaluate(self) -> bool:
		opening = self.context.get("opening_odometer")
		closing = self.context.get("closing_odometer")
		current_vehicle_odometer = self.context.get("current_vehicle_odometer", 0.0)

		if opening is not None and float(opening) < float(current_vehicle_odometer):
			self.add_violation("ASSIGN-004: Opening Odometer cannot be less than current Vehicle Odometer.")
			return False

		if opening is not None and closing is not None and float(closing) < float(opening):
			self.add_violation("ASSIGN-005: Closing Odometer cannot be less than Opening Odometer.")
			return False

		return True


class AssignmentReadOnlyClosedRule(BaseBusinessRule):
	"""
	Rule ASSIGN-008: Closed or Cancelled assignments are read-only and cannot be re-activated.
	"""

	def evaluate(self) -> bool:
		status = self.context.get("status")
		if status in (AssignmentStatus.CLOSED, AssignmentStatus.CANCELLED):
			self.add_violation(f"ASSIGN-008: Assignment is in '{status}' status and cannot be modified.")
			return False
		return True


class AssignmentCompanyIsolationRule(BaseBusinessRule):
	"""
	Rule ASSIGN-010: Validates multi-company tenant isolation for assignments.
	"""

	def evaluate(self) -> bool:
		vehicle_company = self.context.get("vehicle_company")
		assignment_company = self.context.get("assignment_company")
		if vehicle_company and assignment_company and vehicle_company != assignment_company:
			self.add_violation(f"ASSIGN-010: Cross-company assignment denied: Vehicle belongs to '{vehicle_company}', Assignment belongs to '{assignment_company}'.")
			return False
		return True


# Backward compatible rule class aliases
AssignmentOdometerRule = AssignmentOdometerIntegrityRule
AssignmentOverlapRule = AssignmentActiveDuplicateRule

