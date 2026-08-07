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
		{"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Fleet Vehicle", "width": 140},
		{"label": "Maintenance Activity / Item", "fieldname": "maintenance_type", "fieldtype": "Data", "width": 180},
		{"label": "Date", "fieldname": "maintenance_date", "fieldtype": "Date", "width": 110},
		{"label": "Odometer (KM)", "fieldname": "current_odometer", "fieldtype": "Float", "width": 130},
		{"label": "Cost", "fieldname": "cost", "fieldtype": "Currency", "width": 130},
		{"label": "Vendor", "fieldname": "vendor", "fieldtype": "Link", "options": "Maintenance Vendor", "width": 140},
		{"label": "Status", "fieldname": "docstatus_label", "fieldtype": "Data", "width": 110},
		{"label": "Fleet Company", "fieldname": "company", "fieldtype": "Link", "options": "Fleet Company", "width": 140}
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

	# Query Maintenance Entry joined with individual item lines (Maintenance Entry Item)
	entries = frappe.db.sql(f"""
		SELECT
			me.name,
			me.vehicle,
			me.maintenance_date,
			me.current_odometer,
			me.vendor,
			me.docstatus,
			me.total_cost as entry_total_cost,
			v.company,
			mei.item_name,
			mei.cost as item_cost
		FROM `tabMaintenance Entry` me
		LEFT JOIN `tabMaintenance Entry Item` mei ON mei.parent = me.name
		LEFT JOIN `tabFleet Vehicle` v ON v.name = me.vehicle
		WHERE {conditions}
		ORDER BY me.maintenance_date DESC, me.name DESC, mei.idx ASC
	""", values, as_dict=True) if frappe.db.table_exists("Maintenance Entry") else []

	data = []
	total_maint_cost = 0.0
	submitted_entries_set = set()
	draft_cnt = 0
	type_costs = {}
	docstatus_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}

	for e in entries:
		docstatus = int(e.get("docstatus") or 0)
		status_str = docstatus_map.get(docstatus, "Draft")

		maint_item = e.get("item_name") or "General Servicing"
		item_cost = float(e.get("item_cost") or 0.0)

		# Fallback to entry total cost if item cost is zero and item_name is missing
		if item_cost == 0.0 and not e.get("item_name"):
			item_cost = float(e.get("entry_total_cost") or 0.0)

		if docstatus == 1:
			submitted_entries_set.add(e.name)
			total_maint_cost += item_cost
			type_costs[maint_item] = type_costs.get(maint_item, 0.0) + item_cost
		elif docstatus == 0:
			draft_cnt += 1

		data.append({
			"name": e.name,
			"vehicle": e.get("vehicle") or "",
			"maintenance_type": maint_item,
			"maintenance_date": e.get("maintenance_date"),
			"current_odometer": float(e.get("current_odometer") or 0.0),
			"cost": round(item_cost, 2),
			"vendor": e.get("vendor") or "",
			"docstatus_label": status_str,
			"company": e.get("company") or ""
		})

	submitted_cnt = len(submitted_entries_set)
	avg_item_cost = round(total_maint_cost / len(data), 2) if data else 0.0

	report_summary = [
		{"value": len(data), "indicator": "Blue", "label": "Total Maintenance Activities", "datatype": "Int"},
		{"value": submitted_cnt, "indicator": "Green", "label": "Submitted Entries", "datatype": "Int"},
		{"value": draft_cnt, "indicator": "Orange", "label": "Draft Entries", "datatype": "Int"},
		{"value": round(total_maint_cost, 2), "indicator": "Purple", "label": "Total Spend", "datatype": "Currency"},
		{"value": avg_item_cost, "indicator": "Cyan", "label": "Avg Spend / Activity", "datatype": "Currency"}
	]

	# Sort top maintenance activity spends for chart
	sorted_type_costs = dict(sorted(type_costs.items(), key=lambda x: x[1], reverse=True)[:10])

	chart = {
		"data": {
			"labels": list(sorted_type_costs.keys()) if sorted_type_costs else ["General Servicing"],
			"datasets": [{"name": "Spend by Activity", "values": list(sorted_type_costs.values()) if sorted_type_costs else [0]}]
		},
		"type": "bar",
		"colors": ["#8854d0"]
	}

	return data, report_summary, chart
