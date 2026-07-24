"""
Fleet Settings Single DocType Implementation
Fleet Management System
"""

from frappe.model.document import Document
import frappe
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
