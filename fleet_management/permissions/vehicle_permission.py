"""
Vehicle Domain Security & Permission Architecture
Fleet Management System
"""

from typing import Optional
import frappe
from fleet_management.enums import FleetRole
from fleet_management.permissions.evaluator import PermissionEvaluator
from fleet_management.utils.exceptions import FleetPermissionError


class VehiclePermissionEvaluator:
	"""
	Central Security Evaluator for Vehicle records and lifecycle operations.
	"""

	@staticmethod
	def can_register_vehicle(user: Optional[str] = None) -> bool:
		"""Check if user is authorized to create a vehicle."""
		return PermissionEvaluator.has_role(FleetRole.MANAGER, user) or PermissionEvaluator.has_role(FleetRole.OFFICER, user)

	@staticmethod
	def require_registration_permission(user: Optional[str] = None):
		"""Raise FleetPermissionError if user cannot register vehicles."""
		if not VehiclePermissionEvaluator.can_register_vehicle(user):
			raise FleetPermissionError("Permission denied: Registration requires Fleet Manager or Officer role.")

	@staticmethod
	def can_change_status(user: Optional[str] = None) -> bool:
		"""Check if user can transition vehicle status."""
		return PermissionEvaluator.has_role(FleetRole.MANAGER, user) or PermissionEvaluator.has_role(FleetRole.OFFICER, user)
