"""
Vehicle Image Detail Child DocType Controller
Fleet Management System
"""

import frappe
from frappe.model.document import Document


class VehicleImageDetail(Document):
	"""
	Child Document controller for Vehicle Image attachments.
	"""
	doctype = "Vehicle Image Detail"

	def __init__(self, *args, **kwargs):
		if args and isinstance(args[0], dict) and "doctype" not in args[0]:
			args[0]["doctype"] = self.doctype
		super().__init__(*args, **kwargs)

	def before_insert(self):

		if not self.uploaded_by and hasattr(frappe, "session"):
			self.uploaded_by = frappe.session.user
		if not self.upload_date and hasattr(frappe, "utils"):
			self.upload_date = frappe.utils.nowdate()
