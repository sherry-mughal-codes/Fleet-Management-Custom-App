"""
Fuel Business Invariant Rules Architecture
Fleet Management System
"""

from fleet_management.business_rules.base_rule import BaseBusinessRule
from fleet_management.enums import VehicleStatus


class FuelVehicleRequiredRule(BaseBusinessRule):
	"""
	Rule FUEL-001: Verifies vehicle reference exists and is valid.
	"""

	def evaluate(self) -> bool:
		vehicle = self.context.get("vehicle")
		if not vehicle:
			self.add_violation("FUEL-001: Vehicle reference is required for fuel entries.")
			return False
		return True


class FuelQuantityPositiveRule(BaseBusinessRule):
	"""
	Rule FUEL-003: Fuel quantity must be greater than zero.
	"""

	def evaluate(self) -> bool:
		qty = self.context.get("fuel_qty") or self.context.get("liters")
		if qty is None or float(qty) <= 0:
			self.add_violation("FUEL-003: Fuel quantity must be greater than zero.")
			return False
		return True


class FuelOdometerAdvancementRule(BaseBusinessRule):
	"""
	Rule FUEL-004: Odometer reading must be greater than or equal to previous reading.
	"""

	def evaluate(self) -> bool:
		odometer = self.context.get("odometer")
		previous = self.context.get("previous_odometer", 0.0)
		if odometer is not None and float(odometer) < float(previous):
			self.add_violation(f"FUEL-004: Fuel odometer reading ({odometer}) cannot be less than previous odometer ({previous}).")
			return False
		return True


class FuelMaintenanceLockRule(BaseBusinessRule):
	"""
	Rule FUEL-005: Prevents fuel logging when Vehicle status is Under Maintenance.
	"""

	def evaluate(self) -> bool:
		vehicle_status = self.context.get("vehicle_status")
		if vehicle_status == VehicleStatus.UNDER_MAINTENANCE:
			self.add_violation("FUEL-005: Cannot log fuel entry while vehicle is Under Maintenance.")
			return False
		return True


class FuelDuplicateRule(BaseBusinessRule):
	"""
	Rule FUEL-008: Prevents duplicate fuel entries (same vehicle, same odometer, same timestamp).
	"""

	def evaluate(self) -> bool:
		is_duplicate = self.context.get("is_duplicate", False)
		if is_duplicate:
			self.add_violation("FUEL-008: Duplicate fuel entry detected for this vehicle and odometer reading.")
			return False
		return True


class FuelCompanyIsolationRule(BaseBusinessRule):
	"""
	Rule FUEL-010: Validates multi-company tenant isolation for fuel entries.
	"""

	def evaluate(self) -> bool:
		vehicle_company = self.context.get("vehicle_company")
		fuel_company = self.context.get("fuel_company")
		if vehicle_company and fuel_company and vehicle_company != fuel_company:
			self.add_violation(f"FUEL-010: Cross-company fuel entry denied: Vehicle belongs to '{vehicle_company}', Fuel Entry belongs to '{fuel_company}'.")
			return False
		return True
