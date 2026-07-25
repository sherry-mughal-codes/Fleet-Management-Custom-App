"""
Fleet Command Center Setup Script
Creates Number Cards, Dashboard Charts, and Configures Workspaces.
Frappe Framework v15
"""

import json
import frappe


def setup_fleet_dashboards():
	"""Seeds Number Cards, Dashboard Charts, and Workspaces."""
	frappe.set_user("Administrator")

	# ---------------------------------------------------------
	# 1. Number Cards (KPI Metrics)
	# ---------------------------------------------------------
	number_cards = [
		{
			"doctype": "Number Card",
			"name": "Total Fleet Vehicles",
			"label": "Total Fleet Vehicles",
			"type": "Document Type",
			"document_type": "Vehicle",
			"function": "Count",
			"color": "Blue",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Number Card",
			"name": "Available Vehicles",
			"label": "Available Vehicles",
			"type": "Document Type",
			"document_type": "Vehicle",
			"function": "Count",
			"filters_json": json.dumps([["Vehicle", "status", "=", "Available"]]),
			"color": "Green",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Number Card",
			"name": "Vehicles Under Maintenance",
			"label": "Vehicles Under Maintenance",
			"type": "Document Type",
			"document_type": "Vehicle",
			"function": "Count",
			"filters_json": json.dumps([["Vehicle", "status", "=", "Under Maintenance"]]),
			"color": "Red",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Number Card",
			"name": "Active Assignments",
			"label": "Active Assignments",
			"type": "Document Type",
			"document_type": "Vehicle Assignment",
			"function": "Count",
			"filters_json": json.dumps([["Vehicle Assignment", "status", "=", "Assigned"]]),
			"color": "Orange",
			"is_public": 1,
			"module": "Fleet Management",
		},

		{
			"doctype": "Number Card",
			"name": "Total Fuel Spend",
			"label": "Total Fuel Spend",
			"type": "Document Type",
			"document_type": "Fuel Entry",
			"function": "Sum",
			"aggregate_function_based_on": "total_cost",
			"color": "Cyan",
			"is_public": 1,
			"module": "Fleet Management",
		},


		{
			"doctype": "Number Card",
			"name": "Open Maintenance Requests",
			"label": "Open Maintenance Requests",
			"type": "Document Type",
			"document_type": "Maintenance Request",
			"function": "Count",
			"filters_json": json.dumps([["Maintenance Request", "status", "!=", "Completed"]]),
			"color": "Yellow",
			"is_public": 1,
			"module": "Fleet Management",
		},
	]

	for card_def in number_cards:
		if not frappe.db.exists("Number Card", card_def["name"]):
			doc = frappe.get_doc(card_def)
			doc.insert(ignore_permissions=True)
		else:
			doc = frappe.get_doc("Number Card", card_def["name"])
			doc.update(card_def)
			doc.save(ignore_permissions=True)

	frappe.db.commit()

	# ---------------------------------------------------------

	# 2. Dashboard Charts (Visualizations)
	# ---------------------------------------------------------
	charts = [
		{
			"doctype": "Dashboard Chart",
			"name": "Fleet Vehicle Status Distribution",
			"chart_name": "Fleet Vehicle Status Distribution",
			"chart_type": "Group By",
			"type": "Donut",
			"document_type": "Vehicle",
			"group_by_based_on": "status",
			"group_by_type": "Count",
			"filters_json": "[]",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Vehicle Category Breakdown",
			"chart_name": "Vehicle Category Breakdown",
			"chart_type": "Group By",
			"type": "Pie",
			"document_type": "Vehicle",
			"group_by_based_on": "vehicle_category",
			"group_by_type": "Count",
			"filters_json": "[]",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Monthly Fuel Expense",
			"chart_name": "Monthly Fuel Expense",
			"chart_type": "Sum",
			"type": "Line",
			"document_type": "Fuel Entry",
			"based_on": "creation",
			"value_based_on": "total_cost",
			"timespan": "Last Year",
			"time_interval": "Monthly",
			"filters_json": "[]",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Maintenance Spend Trend",
			"chart_name": "Maintenance Spend Trend",
			"chart_type": "Sum",
			"type": "Bar",
			"document_type": "Maintenance Work Order",
			"based_on": "creation",
			"value_based_on": "total_cost",
			"timespan": "Last Year",
			"time_interval": "Monthly",
			"filters_json": "[]",
			"is_public": 1,
			"module": "Fleet Management",
		},
	]




	for chart_def in charts:
		if not frappe.db.exists("Dashboard Chart", chart_def["name"]):
			doc = frappe.get_doc(chart_def)
			doc.insert(ignore_permissions=True)
		else:
			doc = frappe.get_doc("Dashboard Chart", chart_def["name"])
			doc.update(chart_def)
			doc.save(ignore_permissions=True)

	frappe.db.commit()


	# ---------------------------------------------------------
	# 3. Create Dedicated "Fleet Dashboard" Workspace
	# ---------------------------------------------------------
	dash_workspace = {
		"doctype": "Workspace",
		"name": "Fleet Dashboard",
		"label": "Fleet Dashboard",
		"title": "Fleet Dashboard",
		"module": "Fleet Management",
		"icon": "dashboard",
		"indicator_color": "green",
		"public": 1,
		"is_hidden": 0,
		"sequence_id": 0.5,
		"number_cards": [
			{"number_card_name": "Total Fleet Vehicles", "label": "Total Vehicles"},
			{"number_card_name": "Available Vehicles", "label": "Available Vehicles"},
			{"number_card_name": "Vehicles Under Maintenance", "label": "Under Maintenance"},
			{"number_card_name": "Active Assignments", "label": "Active Assignments"},
			{"number_card_name": "Total Fuel Spend", "label": "Total Fuel Spend"},
			{"number_card_name": "Open Maintenance Requests", "label": "Open Requests"},
		],
		"charts": [
			{"chart_name": "Fleet Vehicle Status Distribution", "label": "Fleet Vehicle Status"},
			{"chart_name": "Vehicle Category Breakdown", "label": "Category Breakdown"},
			{"chart_name": "Monthly Fuel Expense", "label": "Monthly Fuel Expense"},
			{"chart_name": "Maintenance Spend Trend", "label": "Maintenance Spend Trend"},
		],
		"shortcuts": [
			{"label": "Vehicle Summary Report", "link_to": "Vehicle Summary Report", "type": "Report", "color": "Blue"},
			{"label": "Fuel Efficiency Report", "link_to": "Fuel Efficiency Report", "type": "Report", "color": "Green"},
			{"label": "Maintenance Summary Report", "link_to": "Maintenance Summary Report", "type": "Report", "color": "Orange"},
			{"label": "Fleet Cost Summary Report", "link_to": "Fleet Cost Summary Report", "type": "Report", "color": "Purple"},
		],
		"links": [
			{
				"hidden": 0,
				"is_query_report": 1,
				"label": "📊 Executive Fleet Reports",
				"link_type": "Report",
				"type": "Card Break"
			},
			{
				"hidden": 0,
				"is_query_report": 1,
				"label": "Vehicle Summary Report",
				"link_to": "Vehicle Summary Report",
				"link_type": "Report",
				"type": "Link"
			},
			{
				"hidden": 0,
				"is_query_report": 1,
				"label": "Fuel Efficiency Report",
				"link_to": "Fuel Efficiency Report",
				"link_type": "Report",
				"type": "Link"
			},
			{
				"hidden": 0,
				"is_query_report": 1,
				"label": "Maintenance Summary Report",
				"link_to": "Maintenance Summary Report",
				"link_type": "Report",
				"type": "Link"
			},
			{
				"hidden": 0,
				"is_query_report": 1,
				"label": "Fleet Cost Summary Report",
				"link_to": "Fleet Cost Summary Report",
				"link_type": "Report",
				"type": "Link"
			}
		],
		"content": json.dumps([
			{"type": "header", "data": {"text": "Fleet Analytics & Executive KPI Dashboard", "level": 2}},
			{"type": "number_card", "data": {"number_card_name": "Total Fleet Vehicles"}},
			{"type": "number_card", "data": {"number_card_name": "Available Vehicles"}},
			{"type": "number_card", "data": {"number_card_name": "Vehicles Under Maintenance"}},
			{"type": "number_card", "data": {"number_card_name": "Active Assignments"}},
			{"type": "number_card", "data": {"number_card_name": "Total Fuel Spend"}},
			{"type": "number_card", "data": {"number_card_name": "Open Maintenance Requests"}},
			{"type": "header", "data": {"text": "Fleet Visual Analytics & Charts", "level": 3}},
			{"type": "chart", "data": {"chart_name": "Fleet Vehicle Status Distribution"}},
			{"type": "chart", "data": {"chart_name": "Vehicle Category Breakdown"}},
			{"type": "chart", "data": {"chart_name": "Monthly Fuel Expense"}},
			{"type": "chart", "data": {"chart_name": "Maintenance Spend Trend"}},
			{"type": "header", "data": {"text": "Reports & Analytics", "level": 3}},
			{"type": "card", "data": {"card_name": "📊 Executive Fleet Reports"}}
		])
	}

	if not frappe.db.exists("Workspace", "Fleet Dashboard"):
		doc = frappe.get_doc(dash_workspace)
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("Workspace", "Fleet Dashboard")
		doc.update(dash_workspace)
		doc.save(ignore_permissions=True)

	if frappe.db.exists("Workspace", "Fleet Management"):
		fm_doc = frappe.get_doc("Workspace", "Fleet Management")
		for sc in (fm_doc.shortcuts or []):
			if getattr(sc, "doc_view", None) == "Form":
				sc.doc_view = ""
		fm_doc.set("charts", [
			{"chart_name": "Fleet Vehicle Status Distribution", "label": "Fleet Vehicle Status"},
			{"chart_name": "Monthly Fuel Expense", "label": "Monthly Fuel Spend"}
		])
		fm_doc.save(ignore_permissions=True)

	frappe.db.sql("""
		DELETE FROM `tabWorkspace Link`
		WHERE link_to IN ('Vehicle Image Detail', 'Vehicle Document Detail')
	""")
	frappe.db.commit()
	print("Fleet Dashboard Workspace, Charts, Number Cards & Workspace Links initialized successfully!")


if __name__ == "__main__":
	setup_fleet_dashboards()
