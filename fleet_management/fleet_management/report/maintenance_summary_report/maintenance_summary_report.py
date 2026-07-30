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
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 140},
		{"label": "Maintenance Type", "fieldname": "maintenance_type", "fieldtype": "Data", "width": 160},
		{"label": "Date", "fieldname": "maintenance_date", "fieldtype": "Date", "width": 110},
		{"label": "Odometer (KM)", "fieldname": "current_odometer", "fieldtype": "Float", "width": 130},
		{"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
		{"label": "Vendor", "fieldname": "vendor", "fieldtype": "Link", "options": "Maintenance Vendor", "width": 140},
		{"label": "Status", "fieldname": "docstatus_label", "fieldtype": "Data", "width": 110},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140}
	]


def get_data_and_summary(filters):
	conditions = "1=1"
	values = {}

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND me.maintenance_date BETWEEN %(from_date)s AND %(to_date)s"
		values["from_date"] = filters["from_date"]
		values["to_date"] = filters["to_date"]
	elif filters.get("from_date"):
		conditions += " AND me.maintenance_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]
	elif filters.get("to_date"):
		conditions += " AND me.maintenance_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	if filters.get("vehicle"):
		conditions += " AND me.vehicle = %(vehicle)s"
		values["vehicle"] = filters["vehicle"]

	if filters.get("company"):
		conditions += " AND v.company = %(company)s"
		values["company"] = filters["company"]

	# Direct SQL query — no per-row get_doc needed
	entries = frappe.db.sql(f"""
		SELECT
			me.name,
			me.vehicle,
			me.maintenance_date,
			me.current_odometer,
			me.total_cost,
			me.vendor,
			me.docstatus,
			v.company
		FROM `tabMaintenance Entry` me
		LEFT JOIN `tabVehicle` v ON v.name = me.vehicle
		WHERE {conditions}
		ORDER BY me.maintenance_date DESC, me.creation DESC
	""", values, as_dict=True) if frappe.db.table_exists("Maintenance Entry") else []

	data = []
	total_maint_cost = 0.0
	submitted_cnt = 0
	draft_cnt = 0
	type_costs = {}
	docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}

	for e in entries:
		docstatus = int(e.get("docstatus") or 0)
		status_str = docstatus_map.get(docstatus, "Draft")

		# Resolve maintenance type from items child table
		maint_type = frappe.db.get_value(
			"Maintenance Entry Item",
			{"parent": e.name, "is_completed": 1},
			"item_name"
		) or "General Servicing"

		if docstatus == 1:
			submitted_cnt += 1
		elif docstatus == 0:
			draft_cnt += 1

		total = float(e.get("total_cost") or 0.0)

		if docstatus != 2:
			total_maint_cost += total
			type_costs[maint_type] = type_costs.get(maint_type, 0.0) + total

		data.append({
			"name": e.name,
			"vehicle": e.get("vehicle") or "",
			"maintenance_type": maint_type,
			"maintenance_date": e.get("maintenance_date"),
			"current_odometer": float(e.get("current_odometer") or 0.0),
			"total_cost": total,
			"vendor": e.get("vendor") or "",
			"docstatus_label": status_str,
			"company": e.get("company") or ""
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

