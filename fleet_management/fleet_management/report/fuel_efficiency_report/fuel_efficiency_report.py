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
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Fleet Vehicle", "width": 140},
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
		{"label": "Fleet Company", "fieldname": "company", "fieldtype": "Link", "options": "Fleet Company", "width": 140},
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

	if filters.get("vehicle"):
		conditions["vehicle"] = filters.get("vehicle")

	# Fetch all submitted fuel entries ordered chronologically by odometer / date
	entries = frappe.get_all(
		"Fuel Entry",
		filters=conditions,
		fields=[
			"name", "vehicle", "fuel_date", "odometer", "fuel_qty",
			"fuel_price", "total_cost", "fuel_type", "fuel_station_name"
		],
		order_by="odometer asc, fuel_date asc, creation asc"
	) if hasattr(frappe, "get_all") else []

	# Build vehicle map with threshold ratings
	v_names = list(set([e.vehicle for e in entries if getattr(e, "vehicle", None)]))
	v_docs = frappe.get_all(
		"Fleet Vehicle",
		filters={"name": ["in", v_names]},
		fields=[
			"name", "vehicle_name", "company", "initial_odometer",
			"excellent_fuel_threshold", "good_fuel_threshold",
			"average_fuel_threshold", "poor_fuel_threshold"
		]
	) if v_names else []
	v_map = {v.name: v for v in v_docs}

	# Resolve driver from active assignment per vehicle
	driver_map = {}
	for v_id in v_names:
		asn = frappe.db.get_value("Vehicle Assignment", {"vehicle": v_id, "docstatus": 1}, ["employee"], as_dict=True)
		driver_map[v_id] = asn.employee if asn else ""

	# Calculate distance travelled and fuel average chronologically per vehicle
	vehicle_last_odo = {}
	raw_rows = []

	for e in entries:
		v_id = e.get("vehicle") or ""
		v_doc = v_map.get(v_id) or {}
		v_name = v_doc.get("vehicle_name") if isinstance(v_doc, dict) else getattr(v_doc, "vehicle_name", "")
		comp_id = v_doc.get("company") if isinstance(v_doc, dict) else getattr(v_doc, "company", "")
		emp_id = driver_map.get(v_id, "")

		if filters.get("company") and comp_id != filters.get("company"):
			continue
		if filters.get("employee") and emp_id != filters.get("employee"):
			continue

		curr_odo = float(e.get("odometer") or 0.0)

		# Determine previous odometer
		if v_id in vehicle_last_odo:
			prev_odo = vehicle_last_odo[v_id]
		else:
			initial_odo = float(v_doc.get("initial_odometer") or 0.0) if isinstance(v_doc, dict) else float(getattr(v_doc, "initial_odometer", 0.0) or 0.0)
			prev_odo = initial_odo

		# Update last seen odometer for this vehicle
		vehicle_last_odo[v_id] = curr_odo

		dist = max(round(curr_odo - prev_odo, 2), 0.0) if prev_odo > 0 else 0.0
		qty = float(e.get("fuel_qty") or 0.0)
		cost = float(e.get("total_cost") or 0.0)

		avg = round(dist / qty, 2) if (dist > 0 and qty > 0) else 0.0
		cpkm = round(cost / dist, 2) if (dist > 0 and cost > 0) else 0.0

		# Evaluate Efficiency Rating based on Vehicle DocType thresholds
		rating = "N/A"
		if avg > 0 and isinstance(v_doc, dict):
			t_exc = float(v_doc.get("excellent_fuel_threshold") or 15.0)
			t_good = float(v_doc.get("good_fuel_threshold") or 10.0)
			t_avg = float(v_doc.get("average_fuel_threshold") or 7.0)
			t_poor = float(v_doc.get("poor_fuel_threshold") or 5.0)

			if avg >= t_exc:
				rating = "Excellent"
			elif avg >= t_good:
				rating = "Good"
			elif avg >= t_avg:
				rating = "Average"
			elif avg >= t_poor:
				rating = "Poor"
			else:
				rating = "Critical"

		raw_rows.append({
			"name": e.name,
			"fuel_date": e.get("fuel_date"),
			"vehicle": v_id,
			"vehicle_name": v_name or "",
			"employee": emp_id,
			"odometer": curr_odo,
			"distance_travelled": dist,
			"fuel_qty": qty,
			"total_cost": cost,
			"fuel_average": avg,
			"cost_per_km": cpkm,
			"fuel_efficiency_rating": rating,
			"fuel_type": e.get("fuel_type") or "",
			"fuel_station_name": e.get("fuel_station_name") or "",
			"company": comp_id or "",
			"status": "Submitted"
		})

	# Sort final data by date descending for report view display
	data = sorted(raw_rows, key=lambda x: (str(x.get("fuel_date") or ""), x.get("name")), reverse=True)

	# Aggregate Summary KPIs & Chart
	total_cost = sum(r["total_cost"] for r in data)
	total_qty = sum(r["fuel_qty"] for r in data)
	total_dist = sum(r["distance_travelled"] for r in data)

	valid_averages = [r["fuel_average"] for r in data if r["fuel_average"] > 0]
	overall_avg = round(total_dist / total_qty, 2) if (total_dist > 0 and total_qty > 0) else (round(sum(valid_averages) / len(valid_averages), 2) if valid_averages else 0.0)

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Fuel Entries", "datatype": "Int"},
		{"value": total_cost, "indicator": "Purple", "label": "Total Fuel Spend", "datatype": "Currency"},
		{"value": total_qty, "indicator": "Cyan", "label": "Total Fuel Liters", "datatype": "Float"},
		{"value": overall_avg, "indicator": "Green", "label": "Overall Fuel Average (KM/L)", "datatype": "Float"}
	]

	# Build line chart of trend over fuel dates
	dates_dict = {}
	for r in sorted(raw_rows, key=lambda x: str(x.get("fuel_date") or "")):
		f_date = str(r.get("fuel_date") or "")
		if f_date and r["fuel_average"] > 0:
			dates_dict[f_date] = r["fuel_average"]

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
