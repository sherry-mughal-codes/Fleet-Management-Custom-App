"""
Vehicle Business Rules Architecture Contract Interface
Fleet Management System
"""

import re

from fleet_management.business_rules.base_rule import BaseBusinessRule
from fleet_management.enums import VehicleStatus


class VehicleAvailabilityRule(BaseBusinessRule):
	"""
	Rule VEH-001: Verifies vehicle availability status for assignments.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("status")
		if vehicle_status != VehicleStatus.AVAILABLE:
			self.add_violation(f"VEH-001: Vehicle status '{vehicle_status}' is not Available for assignment.")
			return False
		return True


class VehicleFuelingMaintenanceRule(BaseBusinessRule):
	"""
	Rule VEH-002: Vehicle cannot receive fuel while Under Maintenance.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("status")
		if vehicle_status == VehicleStatus.UNDER_MAINTENANCE:
			self.add_violation("VEH-002: Vehicle is Under Maintenance and cannot record fuel entries.")
			return False
		return True


class VehicleMaintenanceDueLockRule(BaseBusinessRule):
	"""
	Rule VEH-003: Checks if Maintenance Due lock restricts operations.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("status")
		lock_enabled = self.context.get("maintenance_lock_enabled", False)
		if vehicle_status == VehicleStatus.MAINTENANCE_DUE and lock_enabled:
			self.add_violation("VEH-003: Vehicle is Maintenance Due with strict lock enabled.")
			return False
		return True


class VehicleArchivalAssignmentRule(BaseBusinessRule):
	"""
	Rule VEH-004: Cannot archive a vehicle while currently Assigned.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("status")
		target_status = self.context.get("target_status")
		if target_status == VehicleStatus.ARCHIVED and vehicle_status == VehicleStatus.ASSIGNED:
			self.add_violation("VEH-004: Cannot archive a vehicle while it is currently Assigned.")
			return False
		return True


class VehicleScrapAssignmentRule(BaseBusinessRule):
	"""
	Rule VEH-005: Cannot scrap a vehicle while currently Assigned.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("status")
		target_status = self.context.get("target_status")
		if target_status == VehicleStatus.SCRAPPED and vehicle_status == VehicleStatus.ASSIGNED:
			self.add_violation("VEH-005: Cannot scrap a vehicle while it is currently Assigned.")
			return False
		return True


class VehicleCompanyIsolationRule(BaseBusinessRule):
	"""
	Rule contract enforcing multi-company isolation invariants.
	"""

	def evaluate(self) -> bool:
		vehicle_company = self.context.get("vehicle_company")
		user_company = self.context.get("user_company")
		if vehicle_company and user_company and vehicle_company != user_company:
			self.add_violation(f"Cross-company operation denied: Vehicle belongs to '{vehicle_company}', user belongs to '{user_company}'.")
			return False
		return True


class VehicleVINValidationRule(BaseBusinessRule):
	"""
	Rule contract validating 17-character VIN standard.
	"""

	def evaluate(self) -> bool:
		vin = self.context.get("vin")
		if vin:
			cleaned = str(vin).upper().strip()
			if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", cleaned):
				self.add_violation("VIN must contain exactly 17 uppercase alphanumeric characters.")
				return False
		return True
