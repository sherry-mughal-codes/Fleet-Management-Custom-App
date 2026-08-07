"""
Fleet Company Document Controller
Fleet Management System
"""

import frappe
from frappe.model.document import Document


class FleetCompany(Document):
	"""
	Fleet Company Document Controller.
	"""
	doctype = "Fleet Company"
