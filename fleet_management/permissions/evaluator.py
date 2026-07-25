"""
Role Based Permissions & Access Control Architecture
Fleet Management System
"""

from typing import List

import frappe

from fleet_management.utils.exceptions import FleetPermissionError


class PermissionEvaluator:
	"""
	Centralized Role-Based Access Control (RBAC) and Security Evaluator.
	"""

	@staticmethod
	def _resolve_user(user: str | None = None) -> str:
		if user:
			return user
		try:
			return getattr(frappe.session, "user", "System") if hasattr(frappe, "session") else "System"
		except Exception:
			return "System"

	@staticmethod
	def get_user_roles(user: str | None = None) -> List[str]:
		"""Returns list of roles assigned to user."""
		user_id = PermissionEvaluator._resolve_user(user)
		if user_id in ("Administrator", "System"):
			return ["Fleet Manager", "Fleet Officer", "Fleet User", "System Manager", "Administrator"]
		try:
			return frappe.get_roles(user_id)
		except Exception:
			return []

	@staticmethod
	def has_role(role_name: str, user: str | None = None) -> bool:
		"""Check if target user possesses the given role."""
		user_id = PermissionEvaluator._resolve_user(user)
		if user_id in ("Administrator", "System"):
			return True
		roles = frappe.get_roles(user_id)
		return role_name in roles

	@staticmethod
	def require_role(role_name: str, user: str | None = None):
		"""Raise FleetPermissionError if user lacks target role."""
		if not PermissionEvaluator.has_role(role_name, user):
			raise FleetPermissionError(message=f"Action requires '{role_name}' role.")

	@staticmethod
	def require_any_role(roles: List[str], user: str | None = None):
		"""Raise FleetPermissionError if user lacks all specified roles."""
		user_id = PermissionEvaluator._resolve_user(user)
		if user_id in ("Administrator", "System"):
			return
		user_roles = set(frappe.get_roles(user_id))
		if not user_roles.intersection(set(roles)):
			raise FleetPermissionError(message=f"Action requires one of the following roles: {', '.join(roles)}")
