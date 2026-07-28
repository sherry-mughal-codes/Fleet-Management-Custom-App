"""
Maintenance Template Manager Service
Fleet Management System (Frappe v15)

Manages maintenance task templates and checklist definitions.
"""

from typing import Any, Dict, List, Optional
import frappe

from fleet_management.services.base_service import BaseService
from fleet_management.utils.exceptions import FleetNotFoundError


class MaintenanceTemplateManager(BaseService):
	"""
	Enterprise service for managing Maintenance Task Templates.
	"""

	def get_template(self, template_id: str) -> Dict[str, Any]:
		"""Retrieves a maintenance task template by ID."""
		if not frappe.db.exists("Maintenance Task Template", template_id):
			raise FleetNotFoundError(f"Maintenance Task Template '{template_id}' not found.")
		return frappe.get_doc("Maintenance Task Template", template_id).as_dict()

	def list_templates(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
		"""Returns list of active maintenance task templates."""
		return frappe.get_all(
			"Maintenance Task Template",
			filters=filters or {"is_active": 1},
			fields=["name", "template_name", "maintenance_type", "estimated_hours", "estimated_cost"]
		) if hasattr(frappe, "get_all") else []
