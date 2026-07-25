"""
Role Based Permissions & Access Control Architecture
Fleet Management System
"""

from typing import List, Optional
import frappe
from fleet_management.utils.exceptions import FleetPermissionError

class PermissionEvaluator:
	"""
	Centralized Role-Based Access Control (RBAC) and Security Evaluator.
	"""

	@staticmethod
	def get_user_roles(user: Optional[str] = None) -> List[str]:
		"""Returns list of roles assigned to user."""
		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		if user_id == "Administrator":
			return ["Fleet Manager", "Fleet Officer", "Fleet User", "System Manager", "Administrator"]
		try:
			return frappe.get_roles(user_id)
		except Exception:
			return []

	@staticmethod
	def has_role(role_name: str, user: Optional[str] = None) -> bool:
		"""Check if target user possesses the given role."""
		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		if user_id == "Administrator":
			return True
		roles = frappe.get_roles(user_id)
		return role_name in roles


	@staticmethod
	def require_role(role_name: str, user: Optional[str] = None):
		"""Raise FleetPermissionError if user lacks target role."""
		if not PermissionEvaluator.has_role(role_name, user):
			raise FleetPermissionError(message=f"Action requires '{role_name}' role.")

	@staticmethod
	def require_any_role(roles: List[str], user: Optional[str] = None):
		"""Raise FleetPermissionError if user lacks all specified roles."""
		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		if user_id == "Administrator":
			return
		user_roles = set(frappe.get_roles(user_id))
		if not user_roles.intersection(set(roles)):
			raise FleetPermissionError(message=f"Action requires one of the following roles: {', '.join(roles)}")
