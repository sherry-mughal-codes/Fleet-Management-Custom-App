"""
Migration Patch v2: Populate vehicle field on Maintenance Entry and Fuel Entry
from legacy assignment link, and remove deprecated assignment column.

Fleet Management System (Frappe v15)
"""

import frappe
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.patches.migrate_refactor_v2")


def execute():
	"""
	Data migration for v2 refactor:
	1. Populate Maintenance Entry.vehicle from vehicle_assignment.vehicle where NULL
	2. Populate Fuel Entry.vehicle from vehicle_assignment.vehicle where NULL
	"""
	if not hasattr(frappe, "db") or not frappe.db:
		return

	_migrate_maintenance_entries()
	_migrate_fuel_entries()
	frappe.db.commit()
	logger.info("Refactor v2 migration completed successfully.")


def _migrate_maintenance_entries():
	"""Back-fill vehicle on Maintenance Entry records that still link via assignment."""
	if not frappe.db.table_exists("Maintenance Entry"):
		return

	# Find entries that have assignment but no vehicle
	entries = frappe.db.sql("""
		SELECT name, assignment
		FROM `tabMaintenance Entry`
		WHERE (vehicle IS NULL OR vehicle = '')
		  AND (assignment IS NOT NULL AND assignment != '')
	""", as_dict=True)

	count = 0
	for e in entries:
		vehicle = frappe.db.get_value("Vehicle Assignment", e.assignment, "vehicle")
		if vehicle:
			frappe.db.set_value("Maintenance Entry", e.name, "vehicle", vehicle, update_modified=False)
			count += 1

	if count:
		logger.info(f"Populated vehicle on {count} Maintenance Entry records.")


def _migrate_fuel_entries():
	"""Back-fill vehicle on Fuel Entry records that still link via assignment."""
	if not frappe.db.table_exists("Fuel Entry"):
		return

	# Find entries that have assignment but no vehicle
	entries = frappe.db.sql("""
		SELECT name, assignment
		FROM `tabFuel Entry`
		WHERE (vehicle IS NULL OR vehicle = '')
		  AND (assignment IS NOT NULL AND assignment != '')
	""", as_dict=True)

	count = 0
	for e in entries:
		vehicle = frappe.db.get_value("Vehicle Assignment", e.assignment, "vehicle")
		if vehicle:
			frappe.db.set_value("Fuel Entry", e.name, "vehicle", vehicle, update_modified=False)
			count += 1

	if count:
		logger.info(f"Populated vehicle on {count} Fuel Entry records.")
