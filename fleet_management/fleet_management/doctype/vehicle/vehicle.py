"""
Vehicle Main Document Controller
Fleet Management System
"""

import datetime

import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.services.settings_service import SettingsService
from fleet_management.utils.base_document import BaseFleetDocument
from fleet_management.utils.helpers import get_doc_or_none
from fleet_management.validators.common_validators import validate_date_range, validate_range
from fleet_management.validators.vehicle_asset_validator import (
	VehicleAssetValidator,
	enforce_single_primary_image,
)
from fleet_management.validators.vehicle_validator import VehicleValidator


class Vehicle(BaseFleetDocument):
	"""
	Vehicle Document Controller.
	Enforces Rule IDs VEH-001..VEH-010 and ASSET-001..ASSET-008.
	"""
	doctype = "Vehicle"

	def before_validate_hook(self):
		if not self.status:
			self.status = VehicleStatus.AVAILABLE

		# 1. Run VehicleValidator contract checks (VEH-001..VEH-010)
		VehicleValidator(self.as_dict()).raise_if_invalid()

		# 2. Run VehicleAssetValidator checks (ASSET-001..ASSET-008)
		VehicleAssetValidator(self.as_dict()).raise_if_invalid()

		# 3. Enforce single primary image selection
		if hasattr(self, "images") and self.images:
			enforce_single_primary_image(self.images)

		# 4. Auto-fetch defaults
		if not self.distance_unit:
			self.distance_unit = SettingsService.get_value("default_distance_unit", "KM")
		if not self.fuel_unit:
			self.fuel_unit = SettingsService.get_value("default_fuel_unit", "Liters")
		if not self.company:
			self.company = SettingsService.resolve_default_company()

		# 5. Set default Vehicle Fuel Thresholds if missing
		if not self.excellent_fuel_threshold:
			self.excellent_fuel_threshold = 15.0
		if not self.good_fuel_threshold:
			self.good_fuel_threshold = 10.0
		if not self.average_fuel_threshold:
			self.average_fuel_threshold = 7.0
		if not self.poor_fuel_threshold:
			self.poor_fuel_threshold = 5.0

		# 6. Auto-fetch Model defaults if blank
		if self.vehicle_model:
			model_doc = get_doc_or_none("Vehicle Model", self.vehicle_model)
			if model_doc:
				if not self.fuel_type and model_doc.fuel_type:
					self.fuel_type = model_doc.fuel_type
				if not self.expected_fuel_average and model_doc.default_fuel_average:
					self.expected_fuel_average = model_doc.default_fuel_average
				if not self.engine_capacity and model_doc.engine_capacity:
					self.engine_capacity = model_doc.engine_capacity
				if not self.transmission and model_doc.transmission:
					self.transmission = model_doc.transmission

		# 7. Auto-fetch Fuel Type unit if blank
		if self.fuel_type and not self.fuel_unit:
			fuel_type_doc = get_doc_or_none("Fuel Type", self.fuel_type)
			if fuel_type_doc and fuel_type_doc.unit:
				self.fuel_unit = fuel_type_doc.unit

		# 8. Auto-generate Vehicle Name if empty
		if not self.vehicle_name:
			brand_name = self.vehicle_brand or ""
			model_name = self.vehicle_model or ""
			if "-" in model_name:
				model_name = model_name.split("-")[-1].strip()
			self.vehicle_name = f"{brand_name} {model_name} ({self.vehicle_number})".strip()

		# 9. Date & Year Validations
		if self.warranty_start and self.warranty_end:
			validate_date_range(self.warranty_start, self.warranty_end, "Warranty Start", "Warranty End")

		if self.manufacturing_year:
			next_year = datetime.date.today().year + 1
			validate_range(self.manufacturing_year, 1900, next_year, "Manufacturing Year")
