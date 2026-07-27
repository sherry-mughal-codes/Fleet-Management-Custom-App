"""
Quick Demo Data Engine Service Implementation
Fleet Management System v1.0.0

Generates a realistic Pakistani logistics demo dataset for ABC Logistics (Private) Limited.
Enforces idempotency, safe removal, and full business logic verification.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import frappe
from fleet_management.enums import VehicleStatus
from fleet_management.fleet_management.setup_dashboard import setup_fleet_dashboards
from fleet_management.services.assignment_service import AssignmentService
from fleet_management.services.base_service import BaseService
from fleet_management.services.fleet_cost_service import FleetCostService
from fleet_management.services.fuel_service import FuelService
from fleet_management.services.maintenance_service import MaintenanceService
from fleet_management.services.vehicle_service import VehicleService
from fleet_management.utils.logger import get_logger

logger = get_logger("fleet_management.services.demo_data")

DEMO_COMPANY_NAME = "ABC Logistics (Private) Limited"


class DemoDataService(BaseService):
	"""
	Service orchestrating Quick Demo Dataset loading, removal, and reloading.
	"""

	def __init__(self):
		super().__init__()
		self.vehicle_service = VehicleService()
		self.assignment_service = AssignmentService()
		self.fuel_service = FuelService()
		self.maintenance_service = MaintenanceService()
		self.cost_service = FleetCostService()

	def is_demo_data_loaded(self) -> bool:
		"""Checks if the ABC Logistics demo dataset is currently present."""
		if not hasattr(frappe, "db"):
			return False
		return bool(frappe.db.exists("Vehicle", {"company": DEMO_COMPANY_NAME}))

	def get_demo_status(self) -> Dict[str, Any]:
		"""Returns current status of demo dataset in database."""
		if not hasattr(frappe, "db"):
			return {"loaded": False, "company": DEMO_COMPANY_NAME, "vehicles_count": 0}

		loaded = self.is_demo_data_loaded()
		vehicles_count = frappe.db.count("Vehicle", filters={"company": DEMO_COMPANY_NAME}) if loaded else 0
		fuel_entries_count = frappe.db.count("Fuel Entry", filters={"company": DEMO_COMPANY_NAME}) if loaded else 0
		maintenance_count = frappe.db.count("Maintenance Work Order", filters={"company": DEMO_COMPANY_NAME}) if loaded else 0

		return {
			"loaded": loaded,
			"company": DEMO_COMPANY_NAME,
			"vehicles_count": vehicles_count,
			"fuel_entries_count": fuel_entries_count,
			"maintenance_records_count": maintenance_count,
		}

	def load_demo_data(self) -> Dict[str, Any]:
		"""
		Loads complete demo dataset.
		"""
		logger.info(f"Initiating demo data loading for '{DEMO_COMPANY_NAME}'")

		if self.is_demo_data_loaded():
			self.remove_demo_data()

		created_summary = {}

		# 1. Setup Company & Master Data
		company_doc = self._create_demo_company()
		created_summary["company"] = company_doc.name

		brands = self._ensure_master_brands_and_categories()
		created_summary["brands"] = len(brands)

		# 2. Setup 20 Pakistani Driver/Employee Profiles
		employees = self._get_demo_employee_profiles()
		created_summary["employees"] = len(employees)

		# 3. Setup 10 Vehicles
		vehicles = self._create_demo_vehicles(brands)
		created_summary["vehicles"] = len(vehicles)

		# 4. Setup 8 Assignments (Leave 2 Available)
		assignments = self._create_demo_assignments(vehicles, employees)
		created_summary["assignments"] = len(assignments)

		# 5. Setup ~150 Fuel Entries across 6 Months
		fuel_count = self._create_demo_fuel_entries(vehicles, assignments, employees)
		created_summary["fuel_entries"] = fuel_count

		# 6. Setup ~20 Maintenance Records (Requests & Work Orders)
		maint_count = self._create_demo_maintenance_records(vehicles)
		created_summary["maintenance_records"] = maint_count

		# 7. Refresh Dashboard Metrics & Cost Aggregations
		from fleet_management.services.vehicle_service import sync_all_vehicles_operational_summary
		sync_all_vehicles_operational_summary()
		setup_fleet_dashboards()

		if hasattr(frappe, "db") and frappe.db:
			frappe.db.commit()

		logger.info("Demo data loading successfully completed.")
		return {
			"status": "success",
			"message": f"Successfully loaded demo dataset for '{DEMO_COMPANY_NAME}'.",
			"details": created_summary,
		}

	def remove_demo_data(self) -> Dict[str, Any]:
		"""
		Safely purges demo records associated with ABC Logistics and demo vehicles.
		"""
		logger.info(f"Initiating demo data removal for '{DEMO_COMPANY_NAME}'")

		deleted_summary = {}

		if hasattr(frappe, "db") and frappe.db:
			# Get vehicle names for company
			v_records = frappe.get_all(
				"Vehicle",
				filters=[["company", "=", DEMO_COMPANY_NAME]],
				fields=["name"]
			)
			v_names = [r["name"] for r in v_records]

			# Purge in reverse dependency order
			for doctype in [
				"Fuel Entry",
				"Maintenance Work Order",
				"Maintenance Request",
				"Vehicle Assignment",
			]:
				records = frappe.get_all(doctype, filters=[["company", "=", DEMO_COMPANY_NAME]], fields=["name"])
				for r in records:
					try:
						frappe.delete_doc(doctype, r["name"], force=True, ignore_permissions=True)
					except Exception:
						pass
				deleted_summary[doctype] = len(records)

			# Delete Vehicles
			for vn in v_names:
				if frappe.db.exists("Vehicle", vn):
					try:
						frappe.delete_doc("Vehicle", vn, force=True, ignore_permissions=True)
					except Exception:
						pass
			deleted_summary["Vehicle"] = len(v_names)

			# Delete Company
			if frappe.db.exists("Company", DEMO_COMPANY_NAME):
				try:
					frappe.delete_doc("Company", DEMO_COMPANY_NAME, force=True, ignore_permissions=True)
				except Exception:
					pass
				deleted_summary["Company"] = 1

			# Direct DB cleanup for ABC Logistics company records
			for table in ["Fuel Entry", "Maintenance Work Order", "Maintenance Request", "Vehicle Assignment", "Vehicle"]:
				try:
					frappe.db.sql(f"DELETE FROM `tab{table}` WHERE company LIKE %s OR company = %s", ("%ABC Logistics%", DEMO_COMPANY_NAME))
				except Exception:
					pass
			try:
				frappe.db.sql("DELETE FROM `tabCompany` WHERE name LIKE %s OR name = %s OR company_name LIKE %s", ("%ABC Logistics%", DEMO_COMPANY_NAME, "%ABC Logistics%"))
			except Exception:
				pass

			frappe.db.commit()

		try:
			setup_fleet_dashboards()
			if hasattr(frappe, "db") and frappe.db:
				frappe.db.commit()
		except Exception:
			pass

		if hasattr(frappe, "db") and frappe.db:
			frappe.db.sql("DELETE FROM `tabVehicle` WHERE company LIKE %s OR company = %s", ("%ABC Logistics%", DEMO_COMPANY_NAME))
			frappe.db.commit()

		logger.info("Demo data removal completed.")
		return {
			"status": "success",
			"message": f"Successfully removed demo data for '{DEMO_COMPANY_NAME}'.",
			"details": deleted_summary,
		}

	def reload_demo_data(self) -> Dict[str, Any]:
		"""
		Executes complete reset by removing demo data and reloading.
		"""
		logger.info(f"Reloading demo data for '{DEMO_COMPANY_NAME}'")
		self.remove_demo_data()
		return self.load_demo_data()

	# --- Internal Generator Helpers ---

	def _create_demo_company(self) -> Any:
		"""Creates ABC Logistics (Private) Limited Company record."""
		if not frappe.db.exists("Company", DEMO_COMPANY_NAME):
			c = frappe.get_doc({
				"doctype": "Company",
				"company_name": DEMO_COMPANY_NAME,
				"abbr": "ABC-PK",
				"default_currency": "PKR",
				"country": "Pakistan",
				"tax_id": "NTN-9988776-5",
			}).insert(ignore_permissions=True)
			return c
		return frappe.get_doc("Company", DEMO_COMPANY_NAME)

	def _ensure_master_brands_and_categories(self) -> Dict[str, Dict[str, str]]:
		"""Ensures required Vehicle Brands, Categories, Models, Fuel Types, and Colours exist."""
		for ft in ["Gasoline", "Diesel"]:
			if not frappe.db.exists("Fuel Type", ft):
				frappe.get_doc({"doctype": "Fuel Type", "fuel_name": ft, "is_active": 1}).insert(ignore_permissions=True)

		for col in ["White", "Silver"]:
			if not frappe.db.exists("Vehicle Colour", col):
				frappe.get_doc({"doctype": "Vehicle Colour", "colour_name": col, "is_active": 1}).insert(ignore_permissions=True)

		brand_data = {
			"Toyota": [("Corolla", "Sedan"), ("Yaris", "Sedan"), ("Hilux", "Pickup"), ("Hiace", "Van")],
			"Honda": [("Civic", "Sedan"), ("BR-V", "SUV")],
			"Suzuki": [("Alto", "Car"), ("Bolan", "Van")],
			"Hyundai": [("Porter", "Commercial")],
			"Isuzu": [("D-Max", "Pickup")],
		}

		result = {}
		for b_name, models in brand_data.items():
			b_code = b_name.upper()[:3]
			if not frappe.db.exists("Vehicle Brand", b_name):
				frappe.get_doc({"doctype": "Vehicle Brand", "brand_name": b_name, "brand_code": b_code, "is_active": 1}).insert(ignore_permissions=True)

			result[b_name] = {}
			for m_name, cat_name in models:
				cat_code = cat_name.upper()[:3]
				if not frappe.db.exists("Vehicle Category", cat_name):
					frappe.get_doc({"doctype": "Vehicle Category", "category_name": cat_name, "category_code": cat_code, "is_active": 1}).insert(ignore_permissions=True)

				m_code = f"{b_code}-{m_name.upper()[:3]}"
				m_id = frappe.db.exists("Vehicle Model", {"model_name": m_name, "vehicle_brand": b_name})
				if not m_id:
					m_doc = frappe.get_doc({
						"doctype": "Vehicle Model",
						"model_name": m_name,
						"model_code": m_code,
						"vehicle_brand": b_name,
						"vehicle_category": cat_name,
						"is_active": 1,
					}).insert(ignore_permissions=True)
					m_id = m_doc.name
				result[b_name][m_name] = {"model_id": m_id, "category": cat_name}

		return result

	def _get_demo_employee_profiles(self) -> List[Dict[str, Any]]:
		"""Returns 20 Pakistani driver & staff profiles."""
		names = [
			("Tariq Mehmood", "Fleet Manager", "Fleet Management"),
			("Muhammad Ali", "Senior Driver", "Logistics"),
			("Kamran Khan", "Logistics Officer", "Logistics"),
			("Bilal Ahmed", "Fleet Supervisor", "Fleet Management"),
			("Usman Tariq", "Lead Driver", "Operations"),
			("Zainab Bibi", "HR Executive", "HR"),
			("Sanaullah Shaikh", "Workshop Foreman", "Workshop"),
			("Hamza Shah", "Accountant", "Finance"),
			("Faisal Qureshi", "Driver", "Logistics"),
			("Saad Rafiq", "Dispatch Officer", "Operations"),
			("Omar Chaudhry", "Driver", "Logistics"),
			("Asim Riaz", "Mechanic", "Workshop"),
			("Imran Nazir", "Driver", "Operations"),
			("Haris Rauf", "Driver", "Logistics"),
			("Babar Azam", "Logistics Manager", "Logistics"),
			("Mohammad Rizwan", "Operations Coordinator", "Operations"),
			("Shaheen Afridi", "Driver", "Logistics"),
			("Shadab Khan", "Driver", "Logistics"),
			("Fakhar Zaman", "Driver", "Operations"),
			("Naseem Shah", "Admin Assistant", "Administration"),
		]

		profiles = []
		for idx, (emp_name, desig, dept) in enumerate(names, start=101):
			profiles.append({
				"employee": "Administrator",
				"employee_name": emp_name,
				"designation": desig,
				"department": dept,
				"cell_number": f"+92 300 555{idx}",
			})
		return profiles

	def _create_demo_vehicles(self, brands: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Creates 10 Pakistani vehicles."""
		specs = [
			("KAE-1024", "Corolla Executive", "Toyota", "Corolla", "Gasoline", 55.0, 13.5, 12000.0, 18500.0, 30000.0),
			("KAE-2048", "Yaris Fleet City", "Toyota", "Yaris", "Gasoline", 42.0, 15.0, 8000.0, 14200.0, 25000.0),
			("BCN-5891", "Hilux Heavy Hauler", "Toyota", "Hilux", "Diesel", 80.0, 9.5, 25000.0, 34800.0, 45000.0),
			("LES-4412", "Hiace Passenger Van", "Toyota", "Hiace", "Diesel", 70.0, 10.2, 30000.0, 42100.0, 50000.0),
			("ICT-9901", "Civic Premium", "Honda", "Civic", "Gasoline", 47.0, 12.8, 15000.0, 21900.0, 35000.0),
			("KAE-7712", "BR-V Family Utility", "Honda", "BR-V", "Gasoline", 45.0, 12.0, 10000.0, 16400.0, 30000.0),
			("BCN-3341", "Alto City Express", "Suzuki", "Alto", "Gasoline", 27.0, 18.5, 5000.0, 9800.0, 20000.0),
			("LES-8820", "Bolan Cargo Van", "Suzuki", "Bolan", "Gasoline", 36.0, 11.0, 20000.0, 28300.0, 40000.0),
			("KAE-5530", "Porter Light Truck", "Hyundai", "Porter", "Diesel", 65.0, 9.0, 40000.0, 51200.0, 60000.0),
			("ICT-1122", "D-Max Offroad Pickup", "Isuzu", "D-Max", "Diesel", 76.0, 10.0, 18000.0, 26500.0, 40000.0),
		]

		created = []
		for idx, (reg, vname, bname, mname, ftype, cap, eff, init_odo, curr_odo, next_maint) in enumerate(specs, start=1):
			model_info = brands[bname][mname]
			vin = f"PAK{idx:02d}9988776655{idx:02d}"

			v_payload = {
				"vehicle_number": reg,
				"license_plate": reg,
				"vehicle_name": vname,
				"vehicle_brand": bname,
				"vehicle_model": model_info["model_id"],
				"vehicle_category": model_info["category"],
				"company": DEMO_COMPANY_NAME,
				"vin": vin,
				"engine_number": f"ENG-PK-{idx:04d}",
				"manufacturing_year": 2022 + (idx % 3),
				"colour": "White" if idx % 2 == 0 else "Silver",
				"fuel_type": ftype,
				"fuel_capacity": cap,
				"expected_fuel_average": eff,
				"initial_odometer": init_odo,
				"current_odometer": curr_odo,
				"next_maintenance_due_odometer": next_maint,
				"status": "Available",
			}
			try:
				res = self.vehicle_service.create_vehicle(v_payload)
			except Exception as e:
				logger.error(f"Failed creating vehicle {reg}: {getattr(e, 'details', str(e))}")
				raise
			created.append(res)
		return created

	def _create_demo_assignments(self, vehicles: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Assigns 8 vehicles to employees, leaving 2 available."""
		assignments = []
		for i in range(8):
			v_id = vehicles[i].get("name") or vehicles[i].get("vehicle_number")
			emp_info = employees[i]
			curr_odo = float(vehicles[i].get("current_odometer") or 10000.0)

			asn_payload = {
				"vehicle": v_id,
				"employee": emp_info["employee"],
				"employee_name": emp_info["employee_name"],
				"department": emp_info["department"],
				"designation": emp_info["designation"],
				"company": DEMO_COMPANY_NAME,
				"assignment_date": "2026-02-01",
				"expected_return_date": "2026-08-31",
				"purpose": "Logistics Operational Delivery",
				"opening_odometer": curr_odo,
			}
			asn = self.assignment_service.create_assignment(asn_payload)
			asn_id = asn.get("name")
			self.assignment_service.assign_vehicle(asn_id, opening_odometer=curr_odo)
			assignments.append(asn)
		return assignments

	def _create_demo_fuel_entries(self, vehicles: List[Dict[str, Any]], assignments: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> int:
		"""Creates ~150 historical fuel entries over the previous 6 months."""
		count = 0
		start_date = datetime.now() - timedelta(days=180)

		for i, v in enumerate(vehicles):
			v_id = v.get("name") or v.get("vehicle_number")
			init_odo = float(v.get("initial_odometer") or 10000.0)
			curr_odo = float(v.get("current_odometer") or 20000.0)
			tank_cap = float(v.get("fuel_capacity") or 50.0)

			# 15 fuel stops per vehicle spread over 180 days
			odo_step = (curr_odo - init_odo) / 15.0
			running_odo = init_odo

			for step in range(15):
				running_odo += odo_step + random.uniform(-20, 30)
				entry_date = (start_date + timedelta(days=step * 12 + random.randint(0, 2))).strftime("%Y-%m-%d")

				price_per_liter = round(random.uniform(272.50, 289.00), 2)
				liters = round(random.uniform(tank_cap * 0.5, tank_cap * 0.9), 2)
				total_cost = round(liters * price_per_liter, 2)

				fuel_payload = {
					"vehicle": v_id,
					"employee": employees[i % len(employees)]["employee"],
					"company": DEMO_COMPANY_NAME,
					"fuel_date": entry_date,
					"fuel_qty": liters,
					"fuel_price": price_per_liter,
					"total_cost": total_cost,
					"odometer": round(running_odo, 1),
					"assignment": assignments[i].get("name") if i < len(assignments) else None,
				}
				fuel_doc = self.fuel_service.create_fuel_entry(fuel_payload)
				fuel_id = fuel_doc.get("name")
				self.fuel_service.submit_fuel_entry(fuel_id)
				count += 1

		return count

	def _create_demo_maintenance_records(self, vehicles: List[Dict[str, Any]]) -> int:
		"""Creates ~20 maintenance requests and work orders in various operational states."""
		count = 0
		types = ["Preventive", "Corrective", "Emergency", "Inspection"]

		for i, v in enumerate(vehicles):
			v_id = v.get("name") or v.get("vehicle_number")
			curr_odo = float(v.get("current_odometer") or 20000.0)

			# Create 2 maintenance requests per vehicle (20 total)
			for m_idx in range(2):
				req_payload = {
					"vehicle": v_id,
					"maintenance_type": types[(i + m_idx) % len(types)],
					"company": DEMO_COMPANY_NAME,
					"priority": "High" if m_idx == 1 else "Medium",
					"requested_date": (datetime.now() - timedelta(days=90 - m_idx * 40)).strftime("%Y-%m-%d"),
					"description": f"Scheduled Routine Maintenance Check #{m_idx + 1}",
				}
				req = self.maintenance_service.create_request(req_payload)
				req_id = req.get("name")

				# Create Work Order
				wo_payload = {
					"maintenance_request": req_id,
					"vehicle": v_id,
					"company": DEMO_COMPANY_NAME,
					"status": "In Progress",
				}
				wo = self.maintenance_service.create_work_order(wo_payload)
				wo_id = wo.get("name")

				# If vehicle 8, leave Under Maintenance to exercise Maintenance Lock rule
				if i == 8 and m_idx == 1:
					self.vehicle_service.change_status(v_id, VehicleStatus.UNDER_MAINTENANCE)
				# If vehicle 9, set status to Maintenance Due
				elif i == 9 and m_idx == 1:
					self.vehicle_service.change_status(v_id, VehicleStatus.MAINTENANCE_DUE)
				else:
					costs = {
						"labour_cost": round(random.uniform(2500, 8000), 2),
						"parts_cost": round(random.uniform(5000, 25000), 2),
						"external_cost": round(random.uniform(1000, 5000), 2),
						"tax_amount": 500.0,
						"discount_amount": 200.0,
					}
					v_doc = frappe.get_doc("Vehicle", v_id)
					latest_odo = float(v_doc.current_odometer or curr_odo)
					self.maintenance_service.complete_work_order(wo_id, completion_odometer=latest_odo, costs=costs)
					self.vehicle_service.change_status(v_id, VehicleStatus.AVAILABLE if i >= 8 else VehicleStatus.ASSIGNED)

				count += 1
		return count
