"""
Fleet Cost Summary Script Report Implementation
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
		{"label": "Vehicle ID", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Vehicle Name", "fieldname": "vehicle_name", "fieldtype": "Data", "width": 140},
		{"label": "Brand", "fieldname": "brand", "fieldtype": "Link", "options": "Vehicle Brand", "width": 120},
		{"label": "Category", "fieldname": "vehicle_category", "fieldtype": "Link", "options": "Vehicle Category", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": "Distance Travelled (KM)", "fieldname": "distance_travelled", "fieldtype": "Float", "width": 160},
		{"label": "Fuel Liters (L)", "fieldname": "total_fuel_liters", "fieldtype": "Float", "width": 130},
		{"label": "Total Fuel Cost", "fieldname": "total_fuel_cost", "fieldtype": "Currency", "width": 150},
		{"label": "Total Maintenance Cost", "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 180},
		{"label": "Total Operating Cost", "fieldname": "total_operating_cost", "fieldtype": "Currency", "width": 180},
		{"label": "Cost per KM", "fieldname": "cost_per_km", "fieldtype": "Currency", "width": 120}
	]


def get_data_and_summary(filters):
	v_conditions = {}
	if filters.get("company"):
		v_conditions["company"] = filters.get("company")
	if filters.get("vehicle"):
		v_conditions["name"] = filters.get("vehicle")
	if filters.get("vehicle_brand"):
		v_conditions["vehicle_brand"] = filters.get("vehicle_brand")
	if filters.get("vehicle_category"):
		v_conditions["vehicle_category"] = filters.get("vehicle_category")

	vehicles = frappe.get_all(
		"Vehicle",
		filters=v_conditions,
		fields=["name", "vehicle_name", "vehicle_brand", "vehicle_category", "company", "current_odometer", "initial_odometer"],
		order_by="name asc"
	) if hasattr(frappe, "get_all") else []

	data = []
	grand_fuel_cost = 0.0
	grand_fuel_liters = 0.0
	grand_maint_cost = 0.0
	grand_operating_cost = 0.0
	grand_distance = 0.0

	for v in vehicles:
		current_odo = float(v.get("current_odometer") or 0.0)
		initial_odo = float(v.get("initial_odometer") or 0.0)
		dist = max(0.0, current_odo - initial_odo)

		# Fuel entries for vehicle
		fuel_cond = {"vehicle": v.name, "status": ["!=", "Cancelled"]}
		if filters.get("from_date") and filters.get("to_date"):
			fuel_cond["fuel_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		elif filters.get("from_date"):
			fuel_cond["fuel_date"] = [">=", filters.get("from_date")]
		elif filters.get("to_date"):
			fuel_cond["fuel_date"] = ["<=", filters.get("to_date")]

		fuel_entries = frappe.get_all("Fuel Entry", filters=fuel_cond, fields=["total_cost", "fuel_qty"]) if hasattr(frappe, "get_all") else []
		v_fuel_cost = sum(float(f.get("total_cost") or 0.0) for f in fuel_entries)
		v_fuel_qty = sum(float(f.get("fuel_qty") or 0.0) for f in fuel_entries)

		# Maintenance orders for vehicle
		maint_cond = {"vehicle": v.name, "status": "Completed"}
		if filters.get("from_date") and filters.get("to_date"):
			maint_cond["completion_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		elif filters.get("from_date"):
			maint_cond["completion_date"] = [">=", filters.get("from_date")]
		elif filters.get("to_date"):
			maint_cond["completion_date"] = ["<=", filters.get("to_date")]

		maint_orders = frappe.get_all("Maintenance Work Order", filters=maint_cond, fields=["total_cost"]) if hasattr(frappe, "get_all") else []
		v_maint_cost = sum(float(m.get("total_cost") or 0.0) for m in maint_orders)

		total_op = round(v_fuel_cost + v_maint_cost, 2)
		cpkm = round(total_op / dist, 2) if dist > 0 else 0.0

		grand_fuel_cost += v_fuel_cost
		grand_fuel_liters += v_fuel_qty
		grand_maint_cost += v_maint_cost
		grand_operating_cost += total_op
		grand_distance += dist

		data.append({
			"vehicle": v.name,
			"vehicle_name": v.get("vehicle_name") or "",
			"brand": v.get("vehicle_brand") or "",
			"vehicle_category": v.get("vehicle_category") or "",
			"company": v.get("company") or "",
			"distance_travelled": dist,
			"total_fuel_liters": v_fuel_qty,
			"total_fuel_cost": v_fuel_cost,
			"total_maintenance_cost": v_maint_cost,
			"total_operating_cost": total_op,
			"cost_per_km": cpkm
		})

	# Sort data by total operating cost desc for chart top 10
	sorted_data = sorted(data, key=lambda x: x["total_operating_cost"], reverse=True)[:10]
	top_cost_labels = [x["vehicle"] for x in sorted_data]
	top_fuel_costs = [x["total_fuel_cost"] for x in sorted_data]
	top_maint_costs = [x["total_maintenance_cost"] for x in sorted_data]

	overall_cpkm = round(grand_operating_cost / grand_distance, 2) if grand_distance > 0 else 0.0

	report_summary = [
		{"value": grand_operating_cost, "indicator": "Purple", "label": "Total Fleet Operating Cost", "datatype": "Currency"},
		{"value": grand_fuel_cost, "indicator": "Blue", "label": "Total Fuel Cost", "datatype": "Currency"},
		{"value": grand_maint_cost, "indicator": "Orange", "label": "Total Maintenance Cost", "datatype": "Currency"},
		{"value": overall_cpkm, "indicator": "Green", "label": "Fleet Average Cost / KM", "datatype": "Currency"}
	]

	chart = {
		"data": {
			"labels": top_cost_labels if top_cost_labels else ["No Data"],
			"datasets": [
				{"name": "Fuel Spend", "values": top_fuel_costs if top_fuel_costs else [0]},
				{"name": "Maintenance Spend", "values": top_maint_costs if top_maint_costs else [0]}
			]
		},
		"type": "bar",
		"colors": ["#007bff", "#fd7e14"]
	}

	return data, report_summary, chart
