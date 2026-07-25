"""
Unit & Integration Tests for Quick Demo Data Engine Service
Fleet Management System
"""

import pytest
import frappe
from fleet_management.services.demo_data_service import DEMO_COMPANY_NAME, DemoDataService


class TestDemoDataService:
	"""Test suite for DemoDataService lifecycle, idempotency, and cleanup."""

	@pytest.fixture(autouse=True)
	def setup_service(self):
		"""Initialize DemoDataService instance."""
		self.service = DemoDataService()

	def test_demo_data_full_lifecycle(self):
		"""
		Verifies full demo data lifecycle: load -> idempotency check -> status -> reload -> remove.
		"""
		# Ensure clean start
		self.service.remove_demo_data()
		assert self.service.is_demo_data_loaded() is False

		# 1. Load Demo Data
		load_res = self.service.load_demo_data()
		assert load_res["status"] == "success"
		assert self.service.is_demo_data_loaded() is True

		status = self.service.get_demo_status()
		assert status["loaded"] is True
		assert status["vehicles_count"] == 10
		assert status["fuel_entries_count"] >= 140
		assert status["maintenance_records_count"] >= 15

		# 2. Idempotency Check (Load again)
		second_load = self.service.load_demo_data()
		assert second_load["status"] == "skipped"

		# 3. Reload Demo Data
		reload_res = self.service.reload_demo_data()
		assert reload_res["status"] == "success"

		# 4. Remove Demo Data
		remove_res = self.service.remove_demo_data()
		assert remove_res["status"] == "success"
		assert self.service.is_demo_data_loaded() is False
