"""
Migration Patch: Convert legacy Maintenance Work Orders to Maintenance Entries
Fleet Management System (Frappe v15)
"""

import frappe
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.patches.migrate_legacy_maintenance")


def execute():
	"""Migrates completed Maintenance Work Orders into Maintenance Entries."""
	if not hasattr(frappe, "db") or not frappe.db:
		return

	if not frappe.db.exists("DocType", "Maintenance Entry"):
		return

	if not frappe.db.table_exists("Maintenance Work Order"):
		return

	work_orders = frappe.db.sql("""
		SELECT name, vehicle, completion_date, completion_odometer, total_cost, company
		FROM `tabMaintenance Work Order`
		WHERE docstatus = 1
	""", as_dict=True)

	migrated_count = 0
	for wo in work_orders:
		vehicle_id = wo.get("vehicle")
		if not vehicle_id:
			continue

		# Check if already migrated
		existing = frappe.db.exists("Maintenance Entry", {"vehicle": vehicle_id, "remarks": f"Migrated from Work Order {wo.name}"})
		if existing:
			continue

		# Active or historical assignment lookup
		assignment = frappe.db.get_value("Vehicle Assignment", {"vehicle": vehicle_id}, "name")

		try:
			entry = frappe.get_doc({
				"doctype": "Maintenance Entry",
				"assignment": assignment or "ASN-MIGRATED-001",
				"vehicle": vehicle_id,
				"company": wo.get("company") or "ABC Logistics (Private) Limited",
				"maintenance_date": wo.get("completion_date") or frappe.utils.nowdate(),
				"current_odometer": float(wo.get("completion_odometer") or 0.0),
				"maintenance_type": "Engine Oil Change",
				"rate": float(wo.get("total_cost") or 1000.0),
				"qty": 1.0,
				"remarks": f"Migrated from Work Order {wo.name}",
				"docstatus": 1
			})
			entry.flags.ignore_validate = True
			entry.flags.ignore_mandatory = True
			entry.insert(ignore_permissions=True)
			migrated_count += 1
		except Exception as e:
			logger.warning(f"Could not migrate Work Order {wo.name}: {e}")

	frappe.db.commit()
	logger.info(f"Successfully migrated {migrated_count} legacy Maintenance Work Orders to Maintenance Entries.")
