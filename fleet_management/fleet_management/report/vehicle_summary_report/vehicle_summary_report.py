"""
Vehicle Summary Script Report Implementation
Fleet Management System
"""

import frappe
from fleet_management.services.fleet_cost_service import FleetCostService

cost_service = FleetCostService()


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data, report_summary, chart = get_data_and_summary(filters)
	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{"label": "Vehicle ID", "fieldname": "name", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Vehicle Number", "fieldname": "vehicle_number", "fieldtype": "Data", "width": 130},
		{"label": "Vehicle Name", "fieldname": "vehicle_name", "fieldtype": "Data", "width": 140},
		{"label": "Brand", "fieldname": "vehicle_brand", "fieldtype": "Link", "options": "Vehicle Brand", "width": 120},
		{"label": "Model", "fieldname": "vehicle_model", "fieldtype": "Link", "options": "Vehicle Model", "width": 120},
		{"label": "Category", "fieldname": "vehicle_category", "fieldtype": "Link", "options": "Vehicle Category", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": "Maintenance Due", "fieldname": "is_maintenance_due", "fieldtype": "Data", "width": 140},
		{"label": "Assigned User", "fieldname": "current_employee", "fieldtype": "Link", "options": "User", "width": 140},
		{"label": "Current Odometer (KM)", "fieldname": "current_odometer", "fieldtype": "Float", "width": 160},
		{"label": "Fuel Economy (KM/L)", "fieldname": "average_fuel_economy", "fieldtype": "Float", "width": 150},
		{"label": "Total Fuel Cost", "fieldname": "total_fuel_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Total Maintenance Cost", "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Total Operating Cost", "fieldname": "total_operating_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Cost per KM", "fieldname": "cost_per_km", "fieldtype": "Currency", "width": 120},
		{"label": "Next Service Due (KM)", "fieldname": "next_maintenance_due_odometer", "fieldtype": "Float", "width": 160}
	]


def get_data_and_summary(filters):
	conditions = {}
	if filters.get("company"):
		conditions["company"] = filters.get("company")
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	if filters.get("vehicle_brand"):
		conditions["vehicle_brand"] = filters.get("vehicle_brand")
	if filters.get("vehicle_category"):
		conditions["vehicle_category"] = filters.get("vehicle_category")
	if filters.get("fuel_type"):
		conditions["fuel_type"] = filters.get("fuel_type")

	vehicles = frappe.get_all(
		"Vehicle",
		filters=conditions,
		fields=[
			"name", "vehicle_number", "vehicle_name", "vehicle_brand", "vehicle_model",
			"vehicle_category", "company", "status", "current_employee", "current_odometer",
			"initial_odometer", "average_fuel_economy", "total_fuel_cost", "total_maintenance_cost",
			"next_maintenance_due_odometer"
		],
		order_by="vehicle_number asc"
	) if hasattr(frappe, "get_all") else []

	data = []
	total_vehicles = len(vehicles)
	available_cnt = 0
	maintenance_cnt = 0
	maint_due_cnt = 0
	assigned_cnt = 0
	grand_total_operating = 0.0

	status_counts = {}

	for v in vehicles:
		status = v.get("status") or "Available"
		status_counts[status] = status_counts.get(status, 0) + 1

		curr_odo = float(v.get("current_odometer") or 0.0)
		next_due_odo = float(v.get("next_maintenance_due_odometer") or 0.0)

		is_due = (status in ["Maintenance Due", "Under Maintenance"]) or (next_due_odo > 0 and curr_odo >= next_due_odo)

		if status in ["Available"]:
			available_cnt += 1
		elif status in ["Under Maintenance"]:
			maintenance_cnt += 1
		elif status in ["Assigned", "In Use"]:
			assigned_cnt += 1

		if is_due:
			maint_due_cnt += 1

		# Dynamic calculations via FleetCostService or DB aggregation
		v_cost = cost_service.calculate_vehicle_cost(v.name) if hasattr(cost_service, "calculate_vehicle_cost") else {}
		fuel_cost = v_cost.get("total_fuel_cost", float(v.get("total_fuel_cost") or 0.0))
		maint_cost = v_cost.get("total_maintenance_cost", float(v.get("total_maintenance_cost") or 0.0))
		total_operating = v_cost.get("total_operating_cost", fuel_cost + maint_cost)
		cost_km = v_cost.get("cost_per_km", 0.0)

		grand_total_operating += total_operating

		data.append({
			"name": v.name,
			"vehicle_number": v.get("vehicle_number") or "",
			"vehicle_name": v.get("vehicle_name") or "",
			"vehicle_brand": v.get("vehicle_brand") or "",
			"vehicle_model": v.get("vehicle_model") or "",
			"vehicle_category": v.get("vehicle_category") or "",
			"company": v.get("company") or "",
			"status": status,
			"is_maintenance_due": "Yes (Overdue)" if is_due else "No",
			"current_employee": v.get("current_employee") or "",
			"current_odometer": curr_odo,
			"average_fuel_economy": float(v.get("average_fuel_economy") or 0.0),
			"total_fuel_cost": fuel_cost,
			"total_maintenance_cost": maint_cost,
			"total_operating_cost": total_operating,
			"cost_per_km": cost_km,
			"next_maintenance_due_odometer": next_due_odo
		})

	report_summary = [
		{"value": total_vehicles, "indicator": "Blue", "label": "Total Vehicles", "datatype": "Int"},
		{"value": assigned_cnt, "indicator": "Green", "label": "Assigned", "datatype": "Int"},
		{"value": available_cnt, "indicator": "Cyan", "label": "Available", "datatype": "Int"},
		{"value": maint_due_cnt, "indicator": "Red", "label": "Maintenance Due", "datatype": "Int"},
		{"value": grand_total_operating, "indicator": "Purple", "label": "Total Fleet Operating Cost", "datatype": "Currency"}
	]

	chart = {
		"data": {
			"labels": list(status_counts.keys()) if status_counts else ["Available"],
			"datasets": [{"name": "Status Count", "values": list(status_counts.values()) if status_counts else [0]}]
		},
		"type": "donut",
		"colors": ["#28a745", "#007bff", "#ffc107", "#dc3545", "#6c757d", "#17a2b8"]
	}

	return data, report_summary, chart
