"""
Vehicle Summary Script Report Implementation
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
		{"label": "Vehicle ID", "fieldname": "name", "fieldtype": "Link", "options": "Fleet Vehicle", "width": 140},
		{"label": "Vehicle Number", "fieldname": "vehicle_number", "fieldtype": "Data", "width": 130},
		{"label": "Vehicle Name", "fieldname": "vehicle_name", "fieldtype": "Data", "width": 140},
		{"label": "Brand", "fieldname": "vehicle_brand", "fieldtype": "Link", "options": "Vehicle Brand", "width": 120},
		{"label": "Model", "fieldname": "vehicle_model", "fieldtype": "Link", "options": "Vehicle Model", "width": 120},
		{"label": "Category", "fieldname": "vehicle_category", "fieldtype": "Link", "options": "Vehicle Category", "width": 130},
		{"label": "Fleet Company", "fieldname": "company", "fieldtype": "Link", "options": "Fleet Company", "width": 140},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": "Maintenance Due", "fieldname": "is_maintenance_due", "fieldtype": "Data", "width": 140},
		{"label": "Assigned User", "fieldname": "current_employee", "fieldtype": "Link", "options": "User", "width": 140},
		{"label": "Current Odometer (KM)", "fieldname": "current_odometer", "fieldtype": "Float", "width": 160},
		{"label": "Fuel Economy (KM/L)", "fieldname": "average_fuel_economy", "fieldtype": "Float", "width": 150},
		{"label": "Total Fuel Cost", "fieldname": "total_fuel_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Total Maintenance Cost", "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Total Operating Cost", "fieldname": "total_operating_cost", "fieldtype": "Currency", "width": 160},
		{"label": "Cost per KM", "fieldname": "cost_per_km", "fieldtype": "Currency", "width": 120}
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
		"Fleet Vehicle",
		filters=conditions,
		fields=[
			"name", "vehicle_number", "vehicle_name", "vehicle_brand", "vehicle_model",
			"vehicle_category", "company", "status", "initial_odometer"
		],
		order_by="vehicle_number asc"
	) if hasattr(frappe, "get_all") else []

	data = []
	status_counts = {}
	grand_total_operating = 0.0

	# Status color mapping for aligned Chart & KPI visualization
	status_color_map = {
		"Available": "#28a745",        # Green
		"Assigned": "#007bff",         # Blue
		"Maintenance Due": "#dc3545",  # Red
		"Under Maintenance": "#ffc107",# Orange
		"Return Overdue": "#bd2130",   # Dark Red
		"Reserved": "#17a2b8",         # Teal
		"Inspection": "#6c757d"        # Gray
	}

	for v in vehicles:
		v_id = v.name
		status = v.get("status") or "Available"
		status_counts[status] = status_counts.get(status, 0) + 1

		# 1. Fetch dynamic current odometer from max fuel entry or initial_odometer
		max_fuel_odo = frappe.db.get_value("Fuel Entry", {"vehicle": v_id, "docstatus": 1}, "MAX(odometer)") or 0.0
		initial_odo = float(v.get("initial_odometer") or 0.0)
		curr_odo = max(float(max_fuel_odo), initial_odo)

		# 2. Fetch fuel totals & calculate fuel average
		fuel_stats = frappe.db.sql("""
			SELECT SUM(total_cost) as fuel_cost, SUM(fuel_qty) as total_qty,
			       MIN(odometer) as min_odo, MAX(odometer) as max_odo
			FROM `tabFuel Entry`
			WHERE vehicle = %s AND docstatus = 1
		""", (v_id,), as_dict=True)

		total_fuel_cost = 0.0
		total_fuel_qty = 0.0
		min_odo = 0.0
		max_odo = 0.0
		fuel_economy = 0.0

		if fuel_stats and fuel_stats[0].get("fuel_cost") is not None:
			total_fuel_cost = float(fuel_stats[0].get("fuel_cost") or 0.0)
			total_fuel_qty = float(fuel_stats[0].get("total_qty") or 0.0)
			distance_driven_fuel = max(curr_odo - initial_odo, 0.0)
			if total_fuel_qty > 0 and distance_driven_fuel > 0:
				fuel_economy = round(distance_driven_fuel / total_fuel_qty, 2)

		# 3. Fetch maintenance totals
		maint_cost = float(frappe.db.get_value("Maintenance Entry", {"vehicle": v_id, "docstatus": 1}, "SUM(total_cost)") or 0.0)

		# 4. Total operating cost & cost per km
		total_operating = round(total_fuel_cost + maint_cost, 2)
		grand_total_operating += total_operating

		distance_driven = max(curr_odo - initial_odo, 0.0)
		cost_km = round(total_operating / distance_driven, 2) if distance_driven > 0 else 0.0

		# 5. Fetch assigned employee from active assignment
		current_employee = frappe.db.get_value(
			"Vehicle Assignment",
			{"vehicle": v_id, "docstatus": 1, "return_date": ["is", "not set"]},
			"employee"
		) or ""

		# 6. Maintenance due flag check
		is_due = (status in ["Maintenance Due", "Under Maintenance"])

		data.append({
			"name": v_id,
			"vehicle_number": v.get("vehicle_number") or "",
			"vehicle_name": v.get("vehicle_name") or "",
			"vehicle_brand": v.get("vehicle_brand") or "",
			"vehicle_model": v.get("vehicle_model") or "",
			"vehicle_category": v.get("vehicle_category") or "",
			"company": v.get("company") or "",
			"status": status,
			"is_maintenance_due": "Yes (Overdue)" if is_due else "No",
			"current_employee": current_employee,
			"current_odometer": curr_odo,
			"average_fuel_economy": fuel_economy,
			"total_fuel_cost": round(total_fuel_cost, 2),
			"total_maintenance_cost": round(maint_cost, 2),
			"total_operating_cost": total_operating,
			"cost_per_km": cost_km
		})

	# Build KPI Summary cards matching exact status counts
	total_vehicles = len(vehicles)
	available_cnt = status_counts.get("Available", 0)
	assigned_cnt = status_counts.get("Assigned", 0)
	maint_due_cnt = status_counts.get("Maintenance Due", 0)

	report_summary = [
		{"value": total_vehicles, "indicator": "Blue", "label": "Total Vehicles", "datatype": "Int"},
		{"value": available_cnt, "indicator": "Green", "label": "Available", "datatype": "Int"},
		{"value": assigned_cnt, "indicator": "Blue", "label": "Assigned", "datatype": "Int"},
		{"value": maint_due_cnt, "indicator": "Red", "label": "Maintenance Due", "datatype": "Int"},
		{"value": grand_total_operating, "indicator": "Purple", "label": "Total Fleet Operating Cost", "datatype": "Currency"}
	]

	# Build chart with exact matching colors
	chart_labels = list(status_counts.keys()) if status_counts else ["Available"]
	chart_values = list(status_counts.values()) if status_counts else [0]
	chart_colors = [status_color_map.get(lbl, "#6c757d") for lbl in chart_labels]

	chart = {
		"data": {
			"labels": chart_labels,
			"datasets": [{"name": "Status Count", "values": chart_values}]
		},
		"type": "donut",
		"colors": chart_colors
	}

	return data, report_summary, chart
