"""
Vendor & Workshop Summary Script Report Implementation
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
		{"label": "Workshop / Vendor Name", "fieldname": "workshop", "fieldtype": "Data", "width": 180},
		{"label": "Total Jobs", "fieldname": "total_jobs", "fieldtype": "Int", "width": 110},
		{"label": "Completed Jobs", "fieldname": "completed_jobs", "fieldtype": "Int", "width": 130},
		{"label": "In Progress Jobs", "fieldname": "in_progress_jobs", "fieldtype": "Int", "width": 130},
		{"label": "Labour Cost", "fieldname": "total_labour_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Parts Cost", "fieldname": "total_parts_cost", "fieldtype": "Currency", "width": 130},
		{"label": "External Cost", "fieldname": "total_external_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Total Spend", "fieldname": "total_billed", "fieldtype": "Currency", "width": 150},
		{"label": "Average Job Cost", "fieldname": "avg_job_cost", "fieldtype": "Currency", "width": 140},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140}
	]


def get_data_and_summary(filters):
	conditions = {}
	if filters.get("company"):
		conditions["company"] = filters.get("company")
	if filters.get("workshop"):
		conditions["workshop"] = ["like", f"%{filters.get('workshop')}%"]
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
		fields=["name", "workshop", "status", "labour_cost", "parts_cost", "external_cost", "total_cost", "company"]
	) if hasattr(frappe, "get_all") else []

	vendor_map = {}

	for w in work_orders:
		ws_name = (w.get("workshop") or "").strip() or "Unassigned Workshop"
		company = w.get("company") or ""

		if ws_name not in vendor_map:
			vendor_map[ws_name] = {
				"workshop": ws_name,
				"total_jobs": 0,
				"completed_jobs": 0,
				"in_progress_jobs": 0,
				"total_labour_cost": 0.0,
				"total_parts_cost": 0.0,
				"total_external_cost": 0.0,
				"total_billed": 0.0,
				"company": company
			}

		entry = vendor_map[ws_name]
		entry["total_jobs"] += 1

		status = w.get("status") or ""
		if status == "Completed":
			entry["completed_jobs"] += 1
		elif status == "In Progress":
			entry["in_progress_jobs"] += 1

		labour = float(w.get("labour_cost") or 0.0)
		parts = float(w.get("parts_cost") or 0.0)
		external = float(w.get("external_cost") or 0.0)
		total = float(w.get("total_cost") or (labour + parts + external))

		entry["total_labour_cost"] += labour
		entry["total_parts_cost"] += parts
		entry["total_external_cost"] += external
		entry["total_billed"] += total

	data = []
	grand_total_jobs = 0
	grand_completed_jobs = 0
	grand_total_spend = 0.0

	for ws_name, entry in vendor_map.items():
		avg_cost = round(entry["total_billed"] / entry["total_jobs"], 2) if entry["total_jobs"] > 0 else 0.0
		entry["avg_job_cost"] = avg_cost
		data.append(entry)

		grand_total_jobs += entry["total_jobs"]
		grand_completed_jobs += entry["completed_jobs"]
		grand_total_spend += entry["total_billed"]

	data.sort(key=lambda x: x["total_billed"], reverse=True)

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Vendors/Workshops", "datatype": "Int"},
		{"value": grand_total_jobs, "indicator": "Cyan", "label": "Total Work Orders", "datatype": "Int"},
		{"value": grand_completed_jobs, "indicator": "Green", "label": "Completed Orders", "datatype": "Int"},
		{"value": grand_total_spend, "indicator": "Purple", "label": "Total Maintenance Spend", "datatype": "Currency"}
	]

	chart = {
		"data": {
			"labels": [x["workshop"] for x in data[:10]] if data else ["No Data"],
			"datasets": [{"name": "Spend per Vendor", "values": [x["total_billed"] for x in data[:10]] if data else [0]}]
		},
		"type": "bar",
		"colors": ["#fd7e14"]
	}

	return data, report_summary, chart
