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
		{"label": "Distance Travelled (KM)", "fieldname": "distance_since_last_fuel", "fieldtype": "Float", "width": 160},
		{"label": "Fuel Qty (L)", "fieldname": "fuel_qty", "fieldtype": "Float", "width": 120},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Fuel Average (KM/L)", "fieldname": "fuel_average", "fieldtype": "Float", "width": 160},
		{"label": "Station Name", "fieldname": "fuel_station_name", "fieldtype": "Data", "width": 140},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110}
	]


def get_data_and_summary(filters):
	conditions = {}
	if filters.get("company"):
		conditions["company"] = filters.get("company")
	if filters.get("vehicle"):
		conditions["vehicle"] = filters.get("vehicle")
	if filters.get("employee"):
		conditions["employee"] = filters.get("employee")
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	else:
		conditions["status"] = ["!=", "Cancelled"]

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
			"name", "fuel_date", "vehicle", "vehicle_name", "employee", "odometer",
			"distance_since_last_fuel", "fuel_qty", "total_cost", "fuel_average",
			"fuel_station_name", "company", "status"
		],
		order_by="fuel_date desc, creation desc"
	) if hasattr(frappe, "get_all") else []

	data = []
	total_cost = 0.0
	total_qty = 0.0
	total_distance = 0.0
	valid_avg_list = []

	dates_dict = {}

	for e in entries:
		cost = float(e.get("total_cost") or 0.0)
		qty = float(e.get("fuel_qty") or 0.0)
		dist = float(e.get("distance_since_last_fuel") or 0.0)
		avg = float(e.get("fuel_average") or 0.0)

		total_cost += cost
		total_qty += qty
		total_distance += dist
		if avg > 0:
			valid_avg_list.append(avg)

		f_date = str(e.get("fuel_date") or "")
		if f_date:
			dates_dict[f_date] = dates_dict.get(f_date, 0.0) + cost

		data.append({
			"name": e.name,
			"fuel_date": e.get("fuel_date"),
			"vehicle": e.get("vehicle") or "",
			"vehicle_name": e.get("vehicle_name") or "",
			"employee": e.get("employee") or "",
			"odometer": float(e.get("odometer") or 0.0),
			"distance_since_last_fuel": dist,
			"fuel_qty": qty,
			"total_cost": cost,
			"fuel_average": avg,
			"fuel_station_name": e.get("fuel_station_name") or "",
			"company": e.get("company") or "",
			"status": e.get("status") or "Draft"
		})

	fleet_overall_avg = round(total_distance / total_qty, 2) if total_qty > 0 else (round(sum(valid_avg_list) / len(valid_avg_list), 2) if valid_avg_list else 0.0)

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Fuel Entries", "datatype": "Int"},
		{"value": total_cost, "indicator": "Purple", "label": "Total Fuel Spend", "datatype": "Currency"},
		{"value": total_qty, "indicator": "Cyan", "label": "Total Fuel Liters", "datatype": "Float"},
		{"value": fleet_overall_avg, "indicator": "Green", "label": "Overall Fuel Average (KM/L)", "datatype": "Float"}
	]

	# Chart: Daily Fuel Spend timeline
	sorted_dates = sorted(dates_dict.keys())[-10:] if dates_dict else []
	date_values = [dates_dict[d] for d in sorted_dates] if sorted_dates else [0]

	chart = {
		"data": {
			"labels": sorted_dates if sorted_dates else ["No Data"],
			"datasets": [{"name": "Daily Fuel Cost", "values": date_values}]
		},
		"type": "line",
		"colors": ["#007bff"]
	}

	return data, report_summary, chart
