"""
Vehicle Image Detail Child DocType Controller
Fleet Management System
"""

from frappe.model.document import Document
import frappe


class VehicleImageDetail(Document):
	"""
	Child Document controller for Vehicle Image attachments.
	"""

	def before_insert(self):
		if not self.uploaded_by and hasattr(frappe, "session"):
			self.uploaded_by = frappe.session.user
		if not self.upload_date and hasattr(frappe, "utils"):
			self.upload_date = frappe.utils.nowdate()
