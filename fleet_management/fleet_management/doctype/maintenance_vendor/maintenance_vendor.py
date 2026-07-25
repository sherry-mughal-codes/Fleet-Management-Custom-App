"""
Maintenance Vendor Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_range


class MaintenanceVendor(BaseFleetDocument):
	"""
	Maintenance Vendor Master Document Controller.
	Rule IDs: MASTER-009
	"""
	doctype = "Maintenance Vendor"


	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["vendor_name"])
		# MASTER-009: Validate rating range (0.0 - 5.0)
		if self.rating is not None:
			validate_range(float(self.rating), 0.0, 5.0, "Rating")
