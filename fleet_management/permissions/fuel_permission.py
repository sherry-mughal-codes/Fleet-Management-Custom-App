"""
Fuel Domain Security & Permission Architecture
Fleet Management System
"""

from typing import Optional
from fleet_management.enums import FleetRole
from fleet_management.permissions.evaluator import PermissionEvaluator
from fleet_management.utils.exceptions import FleetPermissionError


class FuelPermissionEvaluator:
	"""
	Central Security Evaluator for Fuel Entry records and operations.
	"""

	@staticmethod
	def can_create_fuel_entry(user: Optional[str] = None) -> bool:
		"""Check if user is authorized to create fuel entries."""
		return (
			PermissionEvaluator.has_role(FleetRole.MANAGER, user)
			or PermissionEvaluator.has_role(FleetRole.OFFICER, user)
			or PermissionEvaluator.has_role(FleetRole.DRIVER, user)
			or PermissionEvaluator.has_role(FleetRole.DISPATCHER, user)
		)

	@staticmethod
	def can_verify_fuel_entry(user: Optional[str] = None) -> bool:
		"""Check if user is authorized to verify fuel entries."""
		return PermissionEvaluator.has_role(FleetRole.MANAGER, user) or PermissionEvaluator.has_role(FleetRole.OFFICER, user)

	@staticmethod
	def require_verification_permission(user: Optional[str] = None):
		"""Raise FleetPermissionError if user cannot verify fuel entries."""
		if not FuelPermissionEvaluator.can_verify_fuel_entry(user):
			raise FleetPermissionError("Permission denied: Fuel verification requires Fleet Manager or Officer role.")
