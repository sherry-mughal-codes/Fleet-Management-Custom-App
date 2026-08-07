"""
Unit & Integration Test for Vehicle Operational Summary Synchronization Engine
Fleet Management System
"""

import pytest
import frappe

from fleet_management.services.vehicle_service import (
	sync_all_vehicles_operational_summary,
	sync_vehicle_operational_summary,
)


class TestOperationalSummarySync:
	"""Test suite for operational summary calculations across Vehicles, Fuel Entries, and Maintenance Work Orders."""

	def test_operational_summary_recalculation(self):
		"""Verifies that operational summary fields update cleanly from database records."""
		vehicles = frappe.get_all("Fleet Vehicle", fields=["name", "vehicle_number"])
		if not vehicles:
			pytest.skip("No vehicles available in DB for testing.")

		# Execute bulk sync across all vehicles
		sync_all_vehicles_operational_summary()

		target_v = None
		for v in vehicles:
			if frappe.db.exists("Fleet Vehicle", v["name"]):
				target_v = v["name"]
				break

		if not target_v:
			pytest.skip("No valid vehicle document exists in DB.")

		v_doc = frappe.get_doc("Fleet Vehicle", target_v)

		# Explicitly trigger sync_operational_summary method
		v_doc.sync_operational_summary()

		# Verify non-null and valid data types
		assert v_doc.current_odometer is not None
		assert v_doc.total_fuel_cost >= 0.0
		assert v_doc.total_maintenance_cost >= 0.0
		assert v_doc.lifetime_distance >= 0.0
		assert v_doc.next_maintenance_due_odometer > 0.0
