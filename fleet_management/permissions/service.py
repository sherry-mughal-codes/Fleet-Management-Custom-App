"""
Permission Service Architecture
Fleet Management System
"""

from typing import List, Optional
import frappe
from fleet_management.constants import ALL_FLEET_ROLES
from fleet_management.permissions.evaluator import PermissionEvaluator
from fleet_management.services.base_service import BaseService


class PermissionService(BaseService):
	"""
	Enterprise service managing role evaluations, scope security, and permission query hooks.
	"""

	@staticmethod
	def is_fleet_user(user: Optional[str] = None) -> bool:
		"""Check if user has any Fleet role assigned."""
		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		if user_id == "Administrator":
			return True
		user_roles = set(frappe.get_roles(user_id))
		return bool(user_roles.intersection(set(ALL_FLEET_ROLES)))

	@staticmethod
	def require_fleet_access(user: Optional[str] = None):
		"""Require user to hold at least one Fleet system role."""
		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		if not PermissionService.is_fleet_user(user_id):
			PermissionEvaluator.require_any_role(list(ALL_FLEET_ROLES), user=user_id)

	@staticmethod
	def get_permitted_documents(doctype: str, user: Optional[str] = None) -> List[str]:
		"""Get list of document names permitted for target user."""
		user_id = user or (frappe.session.user if hasattr(frappe, "session") else "System")
		return frappe.get_list(doctype, filters={}, pluck="name", user=user_id)
