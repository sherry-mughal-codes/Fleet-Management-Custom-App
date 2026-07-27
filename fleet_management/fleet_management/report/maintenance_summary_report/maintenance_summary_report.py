"""
Maintenance Summary Script Report Implementation
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
		{"label": "Work Order ID", "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Work Order", "width": 140},
		{"label": "Request Ref", "fieldname": "maintenance_request", "fieldtype": "Link", "options": "Maintenance Request", "width": 140},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Maintenance Type", "fieldname": "maintenance_type", "fieldtype": "Data", "width": 130},
		{"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date", "width": 110},
		{"label": "Completion Date", "fieldname": "completion_date", "fieldtype": "Date", "width": 120},
		{"label": "Workshop", "fieldname": "workshop", "fieldtype": "Data", "width": 140},
		{"label": "Technician", "fieldname": "assigned_technician", "fieldtype": "Link", "options": "User", "width": 130},
		{"label": "Labour Cost", "fieldname": "labour_cost", "fieldtype": "Currency", "width": 120},
		{"label": "Parts Cost", "fieldname": "parts_cost", "fieldtype": "Currency", "width": 120},
		{"label": "External Cost", "fieldname": "external_cost", "fieldtype": "Currency", "width": 120},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140}
	]


def get_data_and_summary(filters):
	conditions = {}
	if filters.get("company"):
		conditions["company"] = filters.get("company")
	if filters.get("vehicle"):
		conditions["vehicle"] = filters.get("vehicle")
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	else:
		conditions["status"] = ["!=", "Cancelled"]

	if filters.get("from_date") and filters.get("to_date"):
		conditions["creation"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["creation"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["creation"] = ["<=", filters.get("to_date")]

	work_orders = frappe.get_all(
		"Maintenance Work Order",
		filters=conditions,
		fields=[
			"name", "maintenance_request", "vehicle", "assigned_technician", "workshop",
			"start_date", "completion_date", "labour_cost", "parts_cost", "external_cost",
			"tax_amount", "discount_amount", "total_cost", "status", "company"
		],
		order_by="creation desc"
	) if hasattr(frappe, "get_all") else []

	# Pre-fetch Maintenance Types from linked Maintenance Requests
	req_type_map = {}
	req_ids = [w.maintenance_request for w in work_orders if w.get("maintenance_request")]
	if req_ids and hasattr(frappe, "get_all"):
		reqs = frappe.get_all("Maintenance Request", filters={"name": ["in", req_ids]}, fields=["name", "maintenance_type"])
		for r in reqs:
			req_type_map[r.name] = r.maintenance_type

	data = []
	total_maint_cost = 0.0
	completed_cnt = 0
	in_progress_cnt = 0
	scheduled_cnt = 0

	status_counts = {}
	type_costs = {}

	for w in work_orders:
		status = w.get("status") or "Draft"
		status_counts[status] = status_counts.get(status, 0) + 1

		if status == "Completed":
			completed_cnt += 1
		elif status == "In Progress":
			in_progress_cnt += 1
		elif status == "Scheduled":
			scheduled_cnt += 1

		maint_type = req_type_map.get(w.maintenance_request) or "General Maintenance"
		labour = float(w.get("labour_cost") or 0.0)
		parts = float(w.get("parts_cost") or 0.0)
		external = float(w.get("external_cost") or 0.0)
		total = float(w.get("total_cost") or (labour + parts + external))

		total_maint_cost += total
		type_costs[maint_type] = type_costs.get(maint_type, 0.0) + total

		data.append({
			"name": w.name,
			"maintenance_request": w.get("maintenance_request") or "",
			"vehicle": w.get("vehicle") or "",
			"maintenance_type": maint_type,
			"start_date": w.get("start_date"),
			"completion_date": w.get("completion_date"),
			"workshop": w.get("workshop") or "",
			"assigned_technician": w.get("assigned_technician") or "",
			"labour_cost": labour,
			"parts_cost": parts,
			"external_cost": external,
			"total_cost": total,
			"status": status,
			"company": w.get("company") or ""
		})

	avg_job_cost = round(total_maint_cost / len(data), 2) if data else 0.0

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Work Orders", "datatype": "Int"},
		{"value": completed_cnt, "indicator": "Green", "label": "Completed Jobs", "datatype": "Int"},
		{"value": in_progress_cnt, "indicator": "Orange", "label": "In Progress", "datatype": "Int"},
		{"value": total_maint_cost, "indicator": "Purple", "label": "Total Maintenance Cost", "datatype": "Currency"},
		{"value": avg_job_cost, "indicator": "Cyan", "label": "Avg Cost / Work Order", "datatype": "Currency"}
	]

	chart = {
		"data": {
			"labels": list(type_costs.keys()) if type_costs else ["General Maintenance"],
			"datasets": [{"name": "Spend by Type", "values": list(type_costs.values()) if type_costs else [0]}]
		},
		"type": "bar",
		"colors": ["#e83e8c"]
	}

	return data, report_summary, chart
