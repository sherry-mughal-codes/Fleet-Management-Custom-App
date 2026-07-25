"""
Unit Tests for Master DocTypes
Fleet Management System
"""

import pytest

from fleet_management.fleet_management.doctype.distance_unit.distance_unit import DistanceUnit
from fleet_management.fleet_management.doctype.fuel_station.fuel_station import FuelStation
from fleet_management.fleet_management.doctype.fuel_type.fuel_type import FuelType
from fleet_management.fleet_management.doctype.fuel_unit.fuel_unit import FuelUnit
from fleet_management.fleet_management.doctype.maintenance_type.maintenance_type import (
	MaintenanceType,
)
from fleet_management.fleet_management.doctype.maintenance_vendor.maintenance_vendor import (
	MaintenanceVendor,
)
from fleet_management.fleet_management.doctype.vehicle_brand.vehicle_brand import VehicleBrand
from fleet_management.fleet_management.doctype.vehicle_category.vehicle_category import (
	VehicleCategory,
)
from fleet_management.fleet_management.doctype.vehicle_colour.vehicle_colour import VehicleColour
from fleet_management.fleet_management.doctype.vehicle_model.vehicle_model import VehicleModel
from fleet_management.utils.exceptions import FleetValidationError


def test_vehicle_brand_validation():
	brand = VehicleBrand({"brand_name": "Toyota", "brand_code": "TOY", "display_order": 1})
	brand.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_brand = VehicleBrand({"brand_name": "", "brand_code": "TOY"})
		invalid_brand.before_validate_hook()


def test_vehicle_model_validation():
	model = VehicleModel({"model_name": "Corolla", "vehicle_brand": "Toyota", "year": 2024, "default_fuel_average": 15.5})
	model.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_model = VehicleModel({"model_name": "Corolla", "vehicle_brand": "Toyota", "year": 1850})
		invalid_model.before_validate_hook()


def test_vehicle_category_validation():
	cat = VehicleCategory({"category_name": "SUV", "default_maintenance_interval": 5000})
	cat.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_cat = VehicleCategory({"category_name": "SUV", "default_maintenance_interval": -100})
		invalid_cat.before_validate_hook()


def test_fuel_type_validation():
	fuel = FuelType({"fuel_name": "Petrol", "default_density": 0.75})
	fuel.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_fuel = FuelType({"fuel_name": "Petrol", "default_density": -0.5})
		invalid_fuel.before_validate_hook()


def test_maintenance_type_validation():
	maint = MaintenanceType({"maintenance_name": "Oil Change", "default_interval_km": 5000, "estimated_duration_hours": 1.5})
	maint.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_maint = MaintenanceType({"maintenance_name": "Oil Change", "default_interval_km": -50})
		invalid_maint.before_validate_hook()


def test_fuel_station_gps_validation():
	station = FuelStation({"station_name": "Shell Central", "latitude": 24.8607, "longitude": 67.0011})
	station.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_station = FuelStation({"station_name": "Shell Central", "latitude": 120.0})
		invalid_station.before_validate_hook()


def test_maintenance_vendor_rating_validation():
	vendor = MaintenanceVendor({"vendor_name": "AutoFix Garage", "rating": 4.5})
	vendor.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_vendor = MaintenanceVendor({"vendor_name": "AutoFix Garage", "rating": 6.5})
		invalid_vendor.before_validate_hook()


def test_vehicle_colour_hex_validation():
	colour = VehicleColour({"colour_name": "Pearl White", "hex_code": "#FFFFFF"})
	colour.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_colour = VehicleColour({"colour_name": "Pearl White", "hex_code": "INVALID_HEX"})
		invalid_colour.before_validate_hook()


def test_distance_unit_validation():
	dist = DistanceUnit({"unit_name": "KM", "conversion_to_km": 1.0})
	dist.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_dist = DistanceUnit({"unit_name": "KM", "conversion_to_km": 0})
		invalid_dist.before_validate_hook()


def test_fuel_unit_validation():
	fuel_unit = FuelUnit({"unit_name": "Litre", "conversion_to_liters": 1.0})
	fuel_unit.before_validate_hook()

	with pytest.raises(FleetValidationError):
		invalid_fuel_unit = FuelUnit({"unit_name": "Litre", "conversion_to_liters": -1.0})
		invalid_fuel_unit.before_validate_hook()
