"""
Maintenance Summary Script Report Implementation
Fleet Management System (Frappe v15)
"""

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data, report_summary, chart = get_data_and_summary(filters)
	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{"label": "Entry ID", "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Entry", "width": 140},
		{"label": "Assignment", "fieldname": "assignment", "fieldtype": "Link", "options": "Vehicle Assignment", "width": 140},
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "User", "width": 130},
		{"label": "Maintenance Type", "fieldname": "maintenance_type", "fieldtype": "Data", "width": 140},
		{"label": "Date", "fieldname": "maintenance_date", "fieldtype": "Date", "width": 110},
		{"label": "Odometer (KM)", "fieldname": "current_odometer", "fieldtype": "Float", "width": 120},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Vendor", "fieldname": "vendor", "fieldtype": "Link", "options": "Maintenance Vendor", "width": 140},
		{"label": "DocStatus", "fieldname": "docstatus_label", "fieldtype": "Data", "width": 110},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140}
	]


def get_data_and_summary(filters):
	conditions = {}
	if filters.get("from_date") and filters.get("to_date"):
		conditions["maintenance_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
	elif filters.get("from_date"):
		conditions["maintenance_date"] = [">=", filters.get("from_date")]
	elif filters.get("to_date"):
		conditions["maintenance_date"] = ["<=", filters.get("to_date")]

	# Fetch Maintenance Entry records
	entries = frappe.get_all(
		"Maintenance Entry",
		filters=conditions,
		fields=["name", "assignment", "maintenance_date", "current_odometer", "total_cost", "vendor", "docstatus"],
		order_by="maintenance_date desc, creation desc"
	) if (hasattr(frappe, "get_all") and frappe.db.exists("DocType", "Maintenance Entry")) else []

	data = []
	total_maint_cost = 0.0
	submitted_cnt = 0
	draft_cnt = 0
	type_costs = {}

	docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}

	for e in entries:
		doc = frappe.get_doc("Maintenance Entry", e.name)
		v_id = doc.vehicle
		emp_id = doc.employee
		comp_id = doc.company

		if filters.get("vehicle") and v_id != filters.get("vehicle"):
			continue
		if filters.get("company") and comp_id != filters.get("company"):
			continue

		docstatus = int(doc.docstatus or 0)
		status_str = docstatus_map.get(docstatus, "Draft")

		if docstatus == 1:
			submitted_cnt += 1
		elif docstatus == 0:
			draft_cnt += 1

		maint_type = doc.maintenance_type
		total = float(doc.total_cost or 0.0)

		if docstatus != 2:
			total_maint_cost += total
			type_costs[maint_type] = type_costs.get(maint_type, 0.0) + total

		data.append({
			"name": doc.name,
			"assignment": doc.assignment or "",
			"vehicle": v_id or "",
			"employee": emp_id or "",
			"maintenance_type": maint_type,
			"maintenance_date": doc.maintenance_date,
			"current_odometer": float(doc.current_odometer or 0.0),
			"total_cost": total,
			"vendor": doc.vendor or "",
			"docstatus_label": status_str,
			"company": comp_id or ""
		})

	avg_entry_cost = round(total_maint_cost / len(data), 2) if data else 0.0

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Maintenance Entries", "datatype": "Int"},
		{"value": submitted_cnt, "indicator": "Green", "label": "Submitted Entries", "datatype": "Int"},
		{"value": draft_cnt, "indicator": "Orange", "label": "Draft Entries", "datatype": "Int"},
		{"value": total_maint_cost, "indicator": "Purple", "label": "Total Spend", "datatype": "Currency"},
		{"value": avg_entry_cost, "indicator": "Cyan", "label": "Avg Spend / Servicing", "datatype": "Currency"}
	]

	chart = {
		"data": {
			"labels": list(type_costs.keys()) if type_costs else ["General Servicing"],
			"datasets": [{"name": "Spend by Type", "values": list(type_costs.values()) if type_costs else [0]}]
		},
		"type": "bar",
		"colors": ["#e83e8c"]
	}

	return data, report_summary, chart
