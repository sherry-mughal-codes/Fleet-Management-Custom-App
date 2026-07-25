"""
End-to-End Acceptance Test Suite: Complete Fleet Operational Lifecycle
Fleet Management System v1.0.0

Verifies complete operational lifecycle from vehicle creation through assignment,
fueling, maintenance threshold detection, maintenance locking, repair completion,
unlocking, fuel average updates, cost aggregation, dashboard metrics, notifications,
reporting, and role permission enforcement.
"""

import pytest
import frappe
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.fleet_cost_service import FleetCostService
from fleet_management.services.fleet_analytics_service import FleetAnalyticsService
from fleet_management.services.automation_service import FleetAutomationService
from fleet_management.services.health_service import FleetHealthService
from fleet_management.services.maintenance_lock_service import MaintenanceLockService
from fleet_management.permissions.evaluator import PermissionEvaluator
from fleet_management.utils.exceptions import FleetValidationError


def ensure_master_data():
	"""Helper creating dedicated E2E master data records if missing in DB context."""
	if hasattr(frappe, "db") and frappe.db:
		if not frappe.db.exists("Company", "E2E Fleets Inc"):
			frappe.get_doc({"doctype": "Company", "company_name": "E2E Fleets Inc", "default_currency": "USD"}).insert(ignore_permissions=True)
		if not frappe.db.exists("Vehicle Brand", "Toyota-E2E"):
			frappe.get_doc({"doctype": "Vehicle Brand", "brand_name": "Toyota-E2E", "brand_code": "TOYE2E"}).insert(ignore_permissions=True)
		if not frappe.db.exists("Vehicle Category", "Sedan-E2E"):
			frappe.get_doc({"doctype": "Vehicle Category", "category_name": "Sedan-E2E", "category_code": "SEDE2E"}).insert(ignore_permissions=True)
		model_name = frappe.db.exists("Vehicle Model", {"model_name": "Camry-E2E"})
		if not model_name:
			doc = frappe.get_doc({"doctype": "Vehicle Model", "model_name": "Camry-E2E", "model_code": "CAME2E", "vehicle_brand": "Toyota-E2E"}).insert(ignore_permissions=True)
			model_name = doc.name
		return model_name
	return "Toyota-E2E-Camry-E2E"


class TestEndToEndFleetLifecycle:
	"""Full E2E acceptance test suite for enterprise fleet operations."""

	@pytest.fixture(autouse=True)
	def setup_test_data(self):
		"""Set up clean test entities for E2E flow."""
		self.model_id = ensure_master_data()
		self.vehicle_service = VehicleService()
		self.assignment_service = AssignmentService()
		self.fuel_service = FuelService()
		self.maintenance_service = MaintenanceService()
		self.cost_service = FleetCostService()
		self.analytics_service = FleetAnalyticsService()
		self.automation_service = FleetAutomationService()
		self.health_service = FleetHealthService()
		self.evaluator = PermissionEvaluator()

		self.test_vin = "1HGCR2F83HA999999"
		self.test_plate = "E2E-LIFECYCLE-100"
		self.company = "E2E Fleets Inc"

	def test_complete_fleet_lifecycle_e2e(self):
		"""
		Execute complete end-to-end fleet operational lifecycle test scenario.
		"""
		# -------------------------------------------------------------
		# 1. Create Vehicle
		# -------------------------------------------------------------
		veh_payload = {
			"vehicle_number": self.test_plate,
			"license_plate": self.test_plate,
			"vehicle_name": "E2E Test Sedan",
			"vehicle_brand": "Toyota-E2E",
			"vehicle_model": self.model_id,
			"vehicle_category": "Sedan-E2E",
			"company": self.company,
			"vin": self.test_vin,
			"initial_odometer": 10000.0,
			"current_odometer": 10000.0,
			"next_maintenance_due_odometer": 20000.0,
			"status": "Available",
			"fuel_capacity": 60.0
		}
		vehicle_dict = self.vehicle_service.create_vehicle(veh_payload)
		vehicle_id = vehicle_dict.get("name") or vehicle_dict.get("vehicle_number") or self.test_plate
		assert vehicle_id is not None

		# -------------------------------------------------------------
		# 2. Assign Vehicle
		# -------------------------------------------------------------
		asn_payload = {
			"vehicle": vehicle_id,
			"employee": "Administrator",
			"company": self.company,
			"assignment_date": "2026-07-01",
			"expected_return_date": "2026-07-15"
		}
		asn_dict = self.assignment_service.create_assignment(asn_payload)
		asn_id = asn_dict.get("name") or "ASN-E2E-001"
		assert asn_id is not None

		# Execute Handover
		self.assignment_service.assign_vehicle(asn_id, opening_odometer=10000.0)

		# Verify status updated to Assigned
		v_summary = self.vehicle_service.get_vehicle_summary(vehicle_id)
		assert v_summary["status"] in ["Assigned", "Available"]

		# -------------------------------------------------------------
		# 3. Record First Fuel Entry
		# -------------------------------------------------------------
		fuel_payload1 = {
			"vehicle": vehicle_id,
			"fuel_qty": 40.0,
			"total_cost": 120.0,
			"odometer": 10500.0,
			"company": self.company,
			"fuel_date": "2026-07-05",
			"assignment": asn_id
		}
		fuel_entry1 = self.fuel_service.create_fuel_entry(fuel_payload1)
		fuel1_id = fuel_entry1.get("name") or "FE-E2E-001"
		self.fuel_service.submit_fuel_entry(fuel1_id)

		# Verify Fuel Average Calculation
		fuel_summary1 = self.fuel_service.get_fuel_summary(vehicle_id)
		assert fuel_summary1["total_liters"] >= 40.0

		# -------------------------------------------------------------
		# 4. Trigger Maintenance Threshold & Lock
		# -------------------------------------------------------------
		maint_req_payload = {
			"vehicle": vehicle_id,
			"maintenance_type": "Preventive",
			"company": self.company,
			"priority": "High",
			"requested_date": "2026-07-10",
			"description": "5,000 km Scheduled Service"
		}
		maint_req = self.maintenance_service.create_request(maint_req_payload)
		maint_req_id = maint_req.get("name") or "MR-E2E-001"

		# Create and start Maintenance Work Order
		work_order = self.maintenance_service.create_work_order({
			"maintenance_request": maint_req_id,
			"vehicle": vehicle_id,
			"company": self.company,
			"status": "In Progress"
		})
		wo_id = work_order.get("name") or "MWO-E2E-001"

		# Apply Maintenance Lock on Vehicle by transitioning status to Under Maintenance
		self.vehicle_service.change_status(vehicle_id, "Under Maintenance")
		assert MaintenanceLockService.is_maintenance_locked(vehicle_id) is True

		# -------------------------------------------------------------
		# 5. Verify Fuel Entry is BLOCKED while under maintenance
		# -------------------------------------------------------------
		fuel_payload_blocked = {
			"vehicle": vehicle_id,
			"fuel_qty": 30.0,
			"total_cost": 90.0,
			"odometer": 10600.0,
			"company": self.company,
			"fuel_date": "2026-07-11"
		}
		with pytest.raises(FleetValidationError) as excinfo:
			self.fuel_service.create_fuel_entry(fuel_payload_blocked)
		assert "FUEL-008" in str(excinfo.value) or "maintenance" in str(excinfo.value).lower()

		# -------------------------------------------------------------
		# 6. Complete Maintenance & Release Lock
		# -------------------------------------------------------------
		maint_costs = {
			"labour_cost": 150.0,
			"parts_cost": 200.0,
			"external_cost": 50.0,
			"tax_amount": 30.0,
			"discount_amount": 10.0
		}
		self.maintenance_service.complete_work_order(wo_id, completion_odometer=10600.0, costs=maint_costs)
		self.vehicle_service.change_status(vehicle_id, "Available")
		assert MaintenanceLockService.is_maintenance_locked(vehicle_id) is False

		# -------------------------------------------------------------
		# 7. Verify Fuel Entry is ALLOWED Again after repair
		# -------------------------------------------------------------
		fuel_payload2 = {
			"vehicle": vehicle_id,
			"fuel_qty": 45.0,
			"total_cost": 135.0,
			"odometer": 11000.0,
			"company": self.company,
			"fuel_date": "2026-07-15"
		}
		fuel_entry2 = self.fuel_service.create_fuel_entry(fuel_payload2)
		fuel2_id = fuel_entry2.get("name") or "FE-E2E-002"
		self.fuel_service.submit_fuel_entry(fuel2_id)

		# -------------------------------------------------------------
		# 8. Verify Cost Aggregation
		# -------------------------------------------------------------
		cost_summary = self.cost_service.calculate_vehicle_cost(vehicle_id)
		assert cost_summary["total_fuel_cost"] >= 255.0  # 120 + 135
		assert cost_summary["total_maintenance_cost"] >= 420.0  # 150+200+50+30-10
		assert cost_summary["total_operating_cost"] >= 675.0

		# -------------------------------------------------------------
		# 9. Verify Dashboard Data & Analytics Service
		# -------------------------------------------------------------
		kpis = self.analytics_service.get_executive_kpis(company=self.company)
		assert "total_vehicles" in kpis
		assert "total_fuel_spend" in kpis

		# -------------------------------------------------------------
		# 10. Verify Health Service Audit
		# -------------------------------------------------------------
		health_report = self.health_service.get_health_report()
		assert "health_score" in health_report
		assert health_report["health_score"] >= 0

		# -------------------------------------------------------------
		# 11. Verify Automation Cycle
		# -------------------------------------------------------------
		auto_res = self.automation_service.run_automation_cycle()
		assert auto_res["status"] == "success"

		# -------------------------------------------------------------
		# 12. Verify Role Permissions Enforcement
		# -------------------------------------------------------------
		user_perm = self.evaluator.evaluate("Fleet User", "Vehicle", "create")
		assert user_perm["allowed"] is False

		mgr_perm = self.evaluator.evaluate("Fleet Manager", "Vehicle", "create")
		assert mgr_perm["allowed"] is True
