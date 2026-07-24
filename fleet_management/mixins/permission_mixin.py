"""
Permission Mixin
Fleet Management System
"""

import frappe
from fleet_management.permissions.evaluator import PermissionEvaluator

class PermissionMixin:
	"""
	Mixin providing document-level permission verification methods.
	"""

	def check_permission(self, ptype: str = "read", user: str = None) -> bool:
		user_id = user or frappe.session.user
		return frappe.has_permission(self.doctype, ptype=ptype, doc=self, user=user_id)

	def require_role(self, role_name: str, user: str = None):
		PermissionEvaluator.require_role(role_name, user=user)
