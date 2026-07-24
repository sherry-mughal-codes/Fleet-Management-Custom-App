"""
Maintenance Domain Permission Evaluator Architecture
Fleet Management System
"""

import frappe
from fleet_management.enums import FleetRole
from fleet_management.permissions.evaluator import PermissionEvaluator
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.permissions.maintenance")


class MaintenancePermissionEvaluator:
	"""
	Evaluates Role-Based Access Control (RBAC) permissions for Maintenance records.
	"""

	@staticmethod
	def can_create_maintenance(user: str) -> bool:
		"""Checks if user has permission to create maintenance requests."""
		roles = PermissionEvaluator.get_user_roles(user)
		allowed_roles = [FleetRole.MANAGER, FleetRole.OFFICER, FleetRole.MECHANIC, "System Manager"]
		return any(r in allowed_roles for r in roles)

	@staticmethod
	def can_override_maintenance_lock(user: str) -> bool:
		"""Checks if user has permission to override maintenance locks (MAINT-008)."""
		roles = PermissionEvaluator.get_user_roles(user)
		allowed_roles = [FleetRole.MANAGER, "System Manager"]
		return any(r in allowed_roles for r in roles)
