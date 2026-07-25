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
	doctype = "Vehicle Document Detail"

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict) and "doctype" not in args[0]:
			args[0]["doctype"] = self.doctype
		super().__init__(*args, **kwargs)

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
