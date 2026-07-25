"""
Fleet Settings Single DocType Implementation
Fleet Management System
"""

import frappe
from frappe.model.document import Document

from fleet_management.constants import FLEET_SETTINGS_CACHE_KEY


class FleetSettings(Document):
	"""
	Singleton document for global application configuration.
	"""

	def on_update(self):
		"""Invalidate Redis cache when settings are saved."""
		try:
			frappe.cache().delete_value(FLEET_SETTINGS_CACHE_KEY)
		except Exception:
			pass

	@frappe.whitelist(allow_guest=True)
	def load_demo_data(self):
		"""DocType method for loading demo data."""
		from fleet_management.services.demo_data_service import DemoDataService
		return DemoDataService().load_demo_data()

	@frappe.whitelist(allow_guest=True)
	def remove_demo_data(self):
		"""DocType method for removing demo data."""
		from fleet_management.services.demo_data_service import DemoDataService
		return DemoDataService().remove_demo_data()

	@frappe.whitelist(allow_guest=True)
	def load_demo_data_button(self):
		"""DocType button handler."""
		return self.load_demo_data()

	@frappe.whitelist(allow_guest=True)
	def remove_demo_data_button(self):
		"""DocType button handler."""
		return self.remove_demo_data()


@frappe.whitelist(allow_guest=True)
def load_demo_data_button(*args, **kwargs):
	"""Module-level RPC method for load demo data."""
	from fleet_management.services.demo_data_service import DemoDataService
	return DemoDataService().load_demo_data()


@frappe.whitelist(allow_guest=True)
def remove_demo_data_button(*args, **kwargs):
	"""Module-level RPC method for remove demo data."""
	from fleet_management.services.demo_data_service import DemoDataService
	return DemoDataService().remove_demo_data()


@frappe.whitelist(allow_guest=True)
def load_demo_data(*args, **kwargs):
	"""Module-level RPC method for load demo data."""
	from fleet_management.services.demo_data_service import DemoDataService
	return DemoDataService().load_demo_data()


@frappe.whitelist(allow_guest=True)
def remove_demo_data(*args, **kwargs):
	"""Module-level RPC method for remove demo data."""
	from fleet_management.services.demo_data_service import DemoDataService
	return DemoDataService().remove_demo_data()
