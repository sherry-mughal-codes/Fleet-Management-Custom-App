"""
Vehicle Document Detail Child DocType Controller
Fleet Management System
"""

import datetime
from frappe.model.document import Document
import frappe


class VehicleDocumentDetail(Document):
	"""
	Child Document controller for Vehicle Document attachments.
	"""

	def get_days_until_expiry(self) -> int:
		"""Calculate remaining days until document expiry."""
		if not self.expiry_date:
			return 999999
		exp = frappe.utils.getdate(self.expiry_date)
		today = frappe.utils.getdate(frappe.utils.nowdate())
		return (exp - today).days

	def is_expired(self) -> bool:
		"""Check if document is expired relative to current date."""
		return self.get_days_until_expiry() < 0
