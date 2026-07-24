"""
Maintenance Type Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_positive_number


class MaintenanceType(BaseFleetDocument):
	"""
	Maintenance Type Master Document Controller.
	Rule IDs: MASTER-007
	"""

	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["maintenance_name"])
		# MASTER-007: Validate maintenance numerical thresholds
		if self.default_interval_km:
			validate_positive_number(self.default_interval_km, "Default Interval", allow_zero=False)
		if self.estimated_duration_hours:
			validate_positive_number(self.estimated_duration_hours, "Estimated Duration Hours", allow_zero=True)
		if self.default_cost:
			validate_positive_number(self.default_cost, "Default Cost", allow_zero=True)
