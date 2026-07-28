"""
Maintenance Template DocType Controller
Fleet Management System (Frappe v15)
"""

from fleet_management.utils.base_document import BaseFleetDocument

class MaintenanceTemplate(BaseFleetDocument):
	"""
	Maintenance Template Master Controller.
	Defines maintenance schedules mapped to Vehicle Categories.
	"""
	doctype = "Maintenance Template"

	def before_validate_hook(self):
		pass
