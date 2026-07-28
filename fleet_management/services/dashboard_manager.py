"""
Dashboard Manager Service
Fleet Management System (Frappe v15)

Centralized dashboard refresh engine providing metrics, counts, and summaries.
"""

from typing import Any, Dict, Optional
import frappe

from fleet_management.enums import VehicleStatus
from fleet_management.services.base_service import BaseService


class DashboardManager(BaseService):
	"""
	Enterprise service for Fleet Dashboard metrics and card summaries.
	"""

	def get_dashboard_summary(self, company: Optional[str] = None) -> Dict[str, Any]:
		"""Returns executive summary metrics for fleet dashboard."""
		filters = {}
		if company:
			filters["company"] = company

		all_vehicles = frappe.get_all("Vehicle", filters=filters, fields=["name", "status"]) if hasattr(frappe, "get_all") else []

		counts = {
			"total_vehicles": len(all_vehicles),
			"available_count": sum(1 for v in all_vehicles if v.get("status") == VehicleStatus.AVAILABLE),
			"assigned_count": sum(1 for v in all_vehicles if v.get("status") == VehicleStatus.ASSIGNED),
			"maintenance_count": sum(1 for v in all_vehicles if v.get("status") in (VehicleStatus.MAINTENANCE_DUE, VehicleStatus.UNDER_MAINTENANCE)),
			"out_of_service_count": sum(1 for v in all_vehicles if v.get("status") == VehicleStatus.OUT_OF_SERVICE),
			"inactive_count": sum(1 for v in all_vehicles if v.get("status") in (VehicleStatus.INACTIVE, VehicleStatus.ARCHIVED))
		}
		return counts

	def refresh_dashboards(self) -> bool:
		"""Triggers setup / refresh of standard desk dashboards."""
		from fleet_management.fleet_management.setup_dashboard import setup_fleet_dashboards
		setup_fleet_dashboards()
		return True
