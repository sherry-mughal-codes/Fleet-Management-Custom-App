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
		if not self.current_assignment_status:
			self.current_assignment_status = "Unassigned"
		if self.current_odometer is None:
			self.current_odometer = float(self.initial_odometer or 0.0)

		# 1. Run VehicleValidator contract checks (VEH-001..VEH-010)
		VehicleValidator(self.as_dict()).raise_if_invalid()

		# 2. Run VehicleAssetValidator checks (ASSET-001..ASSET-008)
		VehicleAssetValidator(self.as_dict()).raise_if_invalid()

		# 3. Enforce single primary image selection
		if hasattr(self, "images") and self.images:
			enforce_single_primary_image(self.images)

		# 4. Auto-fetch Fleet Settings defaults
		if not self.distance_unit:
			self.distance_unit = SettingsService.get_value("default_distance_unit", "KM")
		if not self.fuel_unit:
			self.fuel_unit = SettingsService.get_value("default_fuel_unit", "Liters")
		if not self.company and hasattr(frappe, "defaults"):
			self.company = frappe.defaults.get_user_default("Company")

		# 5. Auto-fetch Model defaults if blank
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

		# 6. Auto-fetch Fuel Type unit if blank
		if self.fuel_type and not self.fuel_unit:
			fuel_type_doc = get_doc_or_none("Fuel Type", self.fuel_type)
			if fuel_type_doc and fuel_type_doc.unit:
				self.fuel_unit = fuel_type_doc.unit

		# 7. Auto-fetch Category maintenance interval if blank
		if self.vehicle_category and not self.maintenance_interval_km:
			cat_doc = get_doc_or_none("Vehicle Category", self.vehicle_category)
			if cat_doc and cat_doc.default_maintenance_interval:
				self.maintenance_interval_km = cat_doc.default_maintenance_interval

		# Fallback to Settings maintenance interval
		if not self.maintenance_interval_km:
			self.maintenance_interval_km = SettingsService.get_maintenance_interval()

		# 8. Auto-generate Vehicle Name if empty
		if not self.vehicle_name:
			brand_name = self.vehicle_brand or ""
			model_name = self.vehicle_model or ""
			if "-" in model_name:
				model_name = model_name.split("-")[-1].strip()
			self.vehicle_name = f"{brand_name} {model_name} ({self.vehicle_number})".strip()

		# 9. Initial & Current Odometer alignment
		if (not self.current_odometer or self.current_odometer == 0) and self.initial_odometer:
			self.current_odometer = float(self.initial_odometer)

		# 10. Calculate Next Maintenance Due Odometer placeholder
		if not self.next_maintenance_due_odometer and self.maintenance_interval_km:
			self.next_maintenance_due_odometer = (self.current_odometer or 0) + self.maintenance_interval_km

		# 11. Date & Year Validations
		if self.warranty_start and self.warranty_end:
			validate_date_range(self.warranty_start, self.warranty_end, "Warranty Start", "Warranty End")

		if self.manufacturing_year:
			next_year = datetime.date.today().year + 1
			validate_range(self.manufacturing_year, 1900, next_year, "Manufacturing Year")

		# 12. Recalculate & Sync Operational Summary from Fuel, Maintenance, and Assignment entries
		if not self.is_new() and self.name:
			self.sync_operational_summary()

	def sync_operational_summary(self):
		"""Recalculates operational summary directly on self before saving using direct SQL aggregation."""
		if not self.name or not hasattr(frappe, "db"):
			return

		initial_odo = float(self.initial_odometer or 0.0)
		current_odo = float(self.current_odometer or initial_odo)
		interval_km = float(self.maintenance_interval_km or 5000.0)

		target_ids = list(set(filter(None, [
			self.name,
			getattr(self, "vehicle_number", None),
			getattr(self, "registration_number", None),
			getattr(self, "license_plate", None)
		])))

		if not target_ids:
			return

		placeholders = ", ".join(["%s"] * len(target_ids))

		# 1. Fuel Entries Aggregation (Direct SQL)
		fuel_entries = frappe.db.sql(f"""
			SELECT total_cost, fuel_date, odometer, fuel_average, status
			FROM `tabFuel Entry`
			WHERE status != 'Cancelled'
			  AND (vehicle IN ({placeholders}) OR vehicle_number IN ({placeholders}))
			ORDER BY fuel_date DESC, creation DESC
		""", tuple(target_ids + target_ids), as_dict=True) if hasattr(frappe.db, "sql") else []

		self.total_fuel_cost = round(sum(float(f.get("total_cost") or 0.0) for f in fuel_entries), 2)
		if fuel_entries:
			self.last_fuel_date = fuel_entries[0].get("fuel_date")

		latest_avg = None
		highest_fuel_odo = initial_odo
		for f in fuel_entries:
			f_odo = float(f.get("odometer") or 0.0)
			if f_odo > highest_fuel_odo:
				highest_fuel_odo = f_odo
			if latest_avg is None and f.get("fuel_average") and float(f.get("fuel_average")) > 0:
				latest_avg = float(f.get("fuel_average"))

		if latest_avg is not None:
			self.average_fuel_economy = latest_avg

		# 2. Maintenance Work Orders & Requests Aggregation (Direct SQL)
		maint_orders = frappe.db.sql(f"""
			SELECT total_cost, completion_date, completion_odometer, status
			FROM `tabMaintenance Work Order`
			WHERE status != 'Cancelled'
			  AND vehicle IN ({placeholders})
			ORDER BY creation DESC
		""", tuple(target_ids), as_dict=True) if hasattr(frappe.db, "sql") else []

		self.total_maintenance_cost = round(sum(float(m.get("total_cost") or 0.0) for m in maint_orders), 2)
		completed_orders = [m for m in maint_orders if m.get("status") == "Completed"]

		if completed_orders:
			self.last_maintenance_date = completed_orders[0].get("completion_date")
			if hasattr(self, "last_maintenance_odometer"):
				self.last_maintenance_odometer = float(completed_orders[0].get("completion_odometer") or 0.0)

		highest_maint_odo = initial_odo
		for m in maint_orders:
			m_odo = float(m.get("completion_odometer") or 0.0)
			if m_odo > highest_maint_odo:
				highest_maint_odo = m_odo

		if not self.last_maintenance_date and hasattr(frappe.db, "sql"):
			m_reqs = frappe.db.sql(f"""
				SELECT requested_date
				FROM `tabMaintenance Request`
				WHERE status != 'Cancelled'
				  AND vehicle IN ({placeholders})
				ORDER BY requested_date DESC
			""", tuple(target_ids), as_dict=True)
			if m_reqs:
				self.last_maintenance_date = m_reqs[0].get("requested_date")

		# 3. Vehicle Assignments Aggregation (Direct SQL)
		assignments = frappe.db.sql(f"""
			SELECT opening_odometer, closing_odometer
			FROM `tabVehicle Assignment`
			WHERE status != 'Cancelled'
			  AND vehicle IN ({placeholders})
		""", tuple(target_ids), as_dict=True) if hasattr(frappe.db, "sql") else []

		highest_assign_odo = initial_odo
		for a in assignments:
			a_open = float(a.get("opening_odometer") or 0.0)
			a_close = float(a.get("closing_odometer") or 0.0)
			if a_open > highest_assign_odo:
				highest_assign_odo = a_open
			if a_close > highest_assign_odo:
				highest_assign_odo = a_close

		# 4. Final Aggregated Metrics & Auto-Updates
		self.current_odometer = max(initial_odo, current_odo, highest_fuel_odo, highest_maint_odo, highest_assign_odo)
		self.lifetime_distance = round(max(0.0, self.current_odometer - initial_odo), 2)

		last_maint_odo = float(getattr(self, "last_maintenance_odometer", 0.0) or 0.0)
		base_due_odo = last_maint_odo if last_maint_odo > 0 else self.current_odometer
		self.next_maintenance_due_odometer = round(base_due_odo + interval_km, 2)
