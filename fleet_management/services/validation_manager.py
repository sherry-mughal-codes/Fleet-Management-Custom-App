"""
Validation Manager Service
Fleet Management System (Frappe v15)

Centralized validation manager housing core domain checks, duplicate verification,
odometer rules, and contract enforcement.
"""

from typing import Any, Dict, Optional
import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetValidationError


class ValidationManager(BaseService):
	"""
	Enterprise service for centralized validations.
	"""

	def validate_duplicate_vehicle(self, vehicle_number: str, exclude_name: Optional[str] = None) -> bool:
		"""Checks if vehicle number is already registered."""
		filters = {"vehicle_number": vehicle_number}
		if exclude_name:
			filters["name"] = ["!=", exclude_name]

		if frappe.db.exists("Vehicle", filters):
			raise FleetValidationError(f"VEH-001: Vehicle Number '{vehicle_number}' already exists.")
		return True

	def validate_duplicate_registration(self, registration_number: str, exclude_name: Optional[str] = None) -> bool:
		"""Checks if registration plate is already registered."""
		if not registration_number:
			return True

		filters = {"registration_number": registration_number}
		if exclude_name:
			filters["name"] = ["!=", exclude_name]

		if frappe.db.exists("Vehicle", filters):
			raise FleetValidationError(f"VEH-002: Registration Number '{registration_number}' already exists.")
		return True

	def validate_odometer(self, new_odometer: float, current_odometer: float) -> bool:
		"""Validates that new odometer reading is non-decreasing."""
		if new_odometer < current_odometer:
			raise FleetValidationError(
				f"ODO-001: New odometer reading ({new_odometer}) cannot be less than current odometer ({current_odometer})."
			)
		return True

	def validate_duplicate_assignment(self, vehicle_id: str, exclude_name: Optional[str] = None) -> bool:
		"""Validates that a vehicle has no other active assignments."""
		filters = {
			"vehicle": vehicle_id,
			"docstatus": 1,
			"return_date": ["is", "not set"],
			"status": ["in", ["Assigned", "In Use", "Approved"]]
		}
		if exclude_name:
			filters["name"] = ["!=", exclude_name]

		if frappe.db.exists("Vehicle Assignment", filters):
			raise FleetValidationError(f"ASN-001: Vehicle '{vehicle_id}' already has an active assignment.")
		return True
