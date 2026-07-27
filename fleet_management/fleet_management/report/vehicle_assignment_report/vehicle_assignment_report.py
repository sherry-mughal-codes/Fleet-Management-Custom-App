"""
Vehicle Assignment Script Report Implementation
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
		{"label": "Assignment ID", "fieldname": "name", "fieldtype": "Link", "options": "Vehicle Assignment", "width": 140},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Vehicle Name", "fieldname": "vehicle_name", "fieldtype": "Data", "width": 140},
		{"label": "Assigned User", "fieldname": "employee", "fieldtype": "Link", "options": "User", "width": 140},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 140},
		{"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 130},
		{"label": "Assignment Date", "fieldname": "assignment_date", "fieldtype": "Date", "width": 120},
		{"label": "Expected Return Date", "fieldname": "expected_return_date", "fieldtype": "Date", "width": 130},
		{"label": "Actual Return Date", "fieldname": "return_date", "fieldtype": "Date", "width": 130},
		{"label": "Opening Odometer (KM)", "fieldname": "opening_odometer", "fieldtype": "Float", "width": 150},
		{"label": "Closing Odometer (KM)", "fieldname": "closing_odometer", "fieldtype": "Float", "width": 150},
		{"label": "Distance Travelled (KM)", "fieldname": "distance_travelled", "fieldtype": "Float", "width": 160},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120}
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
		conditions["assignment_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["assignment_date"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["assignment_date"] = ["<=", filters.get("to_date")]

	assignments = frappe.get_all(
		"Vehicle Assignment",
		filters=conditions,
		fields=[
			"name", "vehicle", "vehicle_name", "employee", "employee_name", "department",
			"company", "assignment_date", "expected_return_date", "return_date",
			"opening_odometer", "closing_odometer", "distance_travelled", "status"
		],
		order_by="assignment_date desc, creation desc"
	) if hasattr(frappe, "get_all") else []

	data = []
	active_cnt = 0
	returned_cnt = 0
	total_distance = 0.0

	status_counts = {}

	for a in assignments:
		status = a.get("status") or "Draft"
		status_counts[status] = status_counts.get(status, 0) + 1

		if status in ["Assigned", "In Use"]:
			active_cnt += 1
		elif status in ["Returned", "Closed"]:
			returned_cnt += 1

		open_odo = float(a.get("opening_odometer") or 0.0)
		close_odo = float(a.get("closing_odometer") or 0.0)
		dist = float(a.get("distance_travelled") or (max(0.0, close_odo - open_odo) if close_odo > 0 else 0.0))

		total_distance += dist

		data.append({
			"name": a.name,
			"vehicle": a.get("vehicle") or "",
			"vehicle_name": a.get("vehicle_name") or "",
			"employee": a.get("employee") or "",
			"employee_name": a.get("employee_name") or "",
			"department": a.get("department") or "",
			"assignment_date": a.get("assignment_date"),
			"expected_return_date": a.get("expected_return_date"),
			"return_date": a.get("return_date"),
			"opening_odometer": open_odo,
			"closing_odometer": close_odo,
			"distance_travelled": dist,
			"company": a.get("company") or "",
			"status": status
		})

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Assignments", "datatype": "Int"},
		{"value": active_cnt, "indicator": "Green", "label": "Active / In-Use", "datatype": "Int"},
		{"value": returned_cnt, "indicator": "Cyan", "label": "Returned / Closed", "datatype": "Int"},
		{"value": total_distance, "indicator": "Purple", "label": "Total Distance Driven (KM)", "datatype": "Float"}
	]

	chart = {
		"data": {
			"labels": list(status_counts.keys()) if status_counts else ["Assigned"],
			"datasets": [{"name": "Assignments", "values": list(status_counts.values()) if status_counts else [0]}]
		},
		"type": "donut",
		"colors": ["#28a745", "#007bff", "#6f42c1", "#e83e8c", "#dc3545"]
	}

	return data, report_summary, chart
