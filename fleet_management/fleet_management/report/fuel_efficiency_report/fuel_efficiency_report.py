"""
Fuel Efficiency Script Report Implementation
Fleet Management System
"""

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data, report_summary, chart = get_data_and_summary(filters)
	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{"label": "Fuel Entry ID", "fieldname": "name", "fieldtype": "Link", "options": "Fuel Entry", "width": 140},
		{"label": "Fuel Date", "fieldname": "fuel_date", "fieldtype": "Date", "width": 110},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Vehicle Name", "fieldname": "vehicle_name", "fieldtype": "Data", "width": 140},
		{"label": "Employee / Driver", "fieldname": "employee", "fieldtype": "Link", "options": "User", "width": 140},
		{"label": "Odometer (KM)", "fieldname": "odometer", "fieldtype": "Float", "width": 130},
		{"label": "Distance Travelled (KM)", "fieldname": "distance_travelled", "fieldtype": "Float", "width": 160},
		{"label": "Fuel Qty (L)", "fieldname": "fuel_qty", "fieldtype": "Float", "width": 120},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Fuel Average (KM/L)", "fieldname": "fuel_average", "fieldtype": "Float", "width": 160},
		{"label": "Cost Per KM", "fieldname": "cost_per_km", "fieldtype": "Currency", "width": 120},
		{"label": "Efficiency Rating", "fieldname": "fuel_efficiency_rating", "fieldtype": "Data", "width": 140},
		{"label": "Fuel Type", "fieldname": "fuel_type", "fieldtype": "Link", "options": "Fuel Type", "width": 120},
		{"label": "Station Name", "fieldname": "fuel_station_name", "fieldtype": "Link", "options": "Fuel Station", "width": 140},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110}
	]


def get_data_and_summary(filters):
	conditions = {"docstatus": 1}

	if filters.get("from_date") and filters.get("to_date"):
		conditions["fuel_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["fuel_date"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["fuel_date"] = ["<=", filters.get("to_date")]

	entries = frappe.get_all(
		"Fuel Entry",
		filters=conditions,
		fields=[
			"name", "assignment", "fuel_date", "odometer", "previous_odometer",
			"distance_travelled", "fuel_qty", "fuel_price", "total_cost", "fuel_average",
			"cost_per_km", "fuel_efficiency_rating", "fuel_type", "fuel_station_name"
		],
		order_by="fuel_date desc, creation desc"
	) if hasattr(frappe, "get_all") else []

	asn_map = {}
	if entries:
		asn_names = list(set([e.assignment for e in entries if getattr(e, "assignment", None)]))
		asns = frappe.get_all(
			"Vehicle Assignment",
			filters={"name": ["in", asn_names]},
			fields=["name", "vehicle", "employee", "company"]
		) if hasattr(frappe, "get_all") else []
		asn_map = {a.name: a for a in asns}

	v_map = {}
	if asn_map:
		v_names = list(set([a.vehicle for a in asn_map.values() if getattr(a, "vehicle", None)]))
		vehicles = frappe.get_all("Vehicle", filters={"name": ["in", v_names]}, fields=["name", "vehicle_name"]) if hasattr(frappe, "get_all") else []
		v_map = {v.name: v.vehicle_name for v in vehicles}

	data = []
	total_cost = 0.0
	total_qty = 0.0
	total_distance = 0.0
	eval_qty = 0.0
	valid_avg_list = []
	dates_dict = {}

	for e in entries:
		asn_doc = asn_map.get(e.assignment) or {}
		v_id = asn_doc.get("vehicle") or ""
		v_name = v_map.get(v_id) or ""
		emp_id = asn_doc.get("employee") or ""
		comp_id = asn_doc.get("company") or ""

		if filters.get("company") and comp_id != filters.get("company"):
			continue
		if filters.get("vehicle") and v_id != filters.get("vehicle"):
			continue
		if filters.get("employee") and emp_id != filters.get("employee"):
			continue

		cost = float(e.get("total_cost") or 0.0)
		qty = float(e.get("fuel_qty") or 0.0)
		dist = float(e.get("distance_travelled") or 0.0)
		avg = float(e.get("fuel_average") or 0.0)
		cpkm = float(e.get("cost_per_km") or 0.0)

		total_cost += cost
		total_qty += qty
		if dist > 0:
			total_distance += dist
			eval_qty += qty

		if avg > 0:
			valid_avg_list.append(avg)

		f_date = str(e.get("fuel_date") or "")
		if f_date and avg > 0:
			dates_dict[f_date] = avg

		data.append({
			"name": e.name,
			"fuel_date": e.get("fuel_date"),
			"vehicle": v_id,
			"vehicle_name": v_name,
			"employee": emp_id,
			"odometer": float(e.get("odometer") or 0.0),
			"distance_travelled": dist,
			"fuel_qty": qty,
			"total_cost": cost,
			"fuel_average": avg,
			"cost_per_km": cpkm,
			"fuel_efficiency_rating": e.get("fuel_efficiency_rating") or "",
			"fuel_type": e.get("fuel_type") or "",
			"fuel_station_name": e.get("fuel_station_name") or "",
			"company": comp_id,
			"status": "Submitted"
		})

	fleet_overall_avg = round(total_distance / eval_qty, 2) if eval_qty > 0 else (round(sum(valid_avg_list) / len(valid_avg_list), 2) if valid_avg_list else 0.0)

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Fuel Entries", "datatype": "Int"},
		{"value": total_cost, "indicator": "Purple", "label": "Total Fuel Spend", "datatype": "Currency"},
		{"value": total_qty, "indicator": "Cyan", "label": "Total Fuel Liters", "datatype": "Float"},
		{"value": fleet_overall_avg, "indicator": "Green", "label": "Overall Fuel Average (KM/L)", "datatype": "Float"}
	]

	sorted_dates = sorted(dates_dict.keys())[-15:] if dates_dict else []
	date_values = [dates_dict[d] for d in sorted_dates] if sorted_dates else [0]

	chart = {
		"data": {
			"labels": sorted_dates if sorted_dates else ["No Data"],
			"datasets": [{"name": "Fleet Fuel Average (KM/L)", "values": date_values}]
		},
		"type": "line",
		"colors": ["#28a745"]
	}

	return data, report_summary, chart
