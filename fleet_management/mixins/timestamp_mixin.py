"""
Timestamp Mixin
Fleet Management System
"""

import frappe

class TimestampMixin:
	"""
	Mixin providing date and time helper utilities for Frappe Documents.
	"""

	def get_creation_date(self):
		return frappe.utils.getdate(getattr(self, "creation", frappe.utils.nowdate()))

	def get_modified_date(self):
		return frappe.utils.getdate(getattr(self, "modified", frappe.utils.nowdate()))

	def days_since_creation((self) -> int:
		created = self.get_creation_date()
		today = frappe.utils.getdate(frappe.utils.nowdate())
		return (today - created).days
