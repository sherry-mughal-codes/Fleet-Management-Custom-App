"""
Fuel Station Controller
Fleet Management System
"""

from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.validators.common_validators import validate_required_fields, validate_range


class FuelStation(BaseFleetDocument):
	"""
	Fuel Station Master Document Controller.
	Rule IDs: MASTER-008
	"""
	doctype = "Fuel Station"


	def before_validate_hook(self):
		validate_required_fields(self.as_dict(), ["station_name"])
		# MASTER-008: Validate GPS coordinates range
		if self.latitude:
			validate_range(self.latitude, -90.0, 90.0, "Latitude")
		if self.longitude:
			validate_range(self.longitude, -180.0, 180.0, "Longitude")
