"""
Maintenance Domain Business Invariant Rules Architecture
Fleet Management System
"""

from typing import Any, Dict
from fleet_management.business_rules.base_rule import BaseBusinessRule
from fleet_management.enums import MaintenanceStatus


class MaintenanceVehicleRequiredRule(BaseBusinessRule):
	"""Rule ID: MAINT-001 - Vehicle reference is required."""

	def evaluate(self) -> bool:
		return bool(self.context.get("vehicle"))

	def get_error_message(self) -> str:
		return "MAINT-001: Vehicle reference is mandatory for maintenance records."


class MaintenanceIntervalRequiredRule(BaseBusinessRule):
	"""Rule ID: MAINT-002 - Maintenance interval (distance or time) required."""

	def evaluate(self) -> bool:
		interval_km = self.context.get("interval_km")
		interval_days = self.context.get("interval_days")
		return bool(interval_km and interval_km > 0) or bool(interval_days and interval_days > 0)

	def get_error_message(self) -> str:
		return "MAINT-002: Maintenance interval (distance or time) must be specified."


class MaintenanceOdometerAdvancementRule(BaseBusinessRule):
	"""Rule ID: MAINT-005 - Vehicle mileage reading cannot decrease."""

	def evaluate(self) -> bool:
		odometer = float(self.context.get("odometer") or 0.0)
		prev_odometer = float(self.context.get("previous_odometer") or 0.0)
		return odometer >= prev_odometer

	def get_error_message(self) -> str:
		return "MAINT-005: Maintenance completion odometer cannot be less than previous odometer."


class MaintenanceReadOnlyCompletedRule(BaseBusinessRule):
	"""Rule ID: MAINT-006 - Completed maintenance records are read-only."""

	def evaluate(self) -> bool:
		current_status = self.context.get("current_status")
		target_status = self.context.get("target_status")
		if current_status == MaintenanceStatus.COMPLETED and target_status and target_status != MaintenanceStatus.COMPLETED:
			return False
		return True

	def get_error_message(self) -> str:
		return "MAINT-006: Completed maintenance records are read-only and cannot be altered."


class MaintenanceCompanyIsolationRule(BaseBusinessRule):
	"""Rule ID: MAINT-010 - Company alignment multi-tenant isolation."""

	def evaluate(self) -> bool:
		maint_company = self.context.get("company")
		vehicle_company = self.context.get("vehicle_company")
		if maint_company and vehicle_company and maint_company != vehicle_company:
			return False
		return True

	def get_error_message(self) -> str:
		return "MAINT-010: Maintenance record company must match Vehicle company."
