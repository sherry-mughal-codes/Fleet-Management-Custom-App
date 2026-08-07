"""
Fleet Command Center Setup Script
Creates Number Cards, Dashboard Charts, and Configures Workspaces.
Frappe Framework v15
"""

import json
import os
import frappe


def setup_fleet_dashboards():
	"""Seeds Number Cards, Dashboard Charts, and Workspaces."""
	frappe.set_user("Administrator")
	try:
		from fleet_management.services.vehicle_service import sync_all_vehicles_operational_summary
		sync_all_vehicles_operational_summary()
	except Exception:
		pass

	# ---------------------------------------------------------
	# 1. Number Cards (KPI Metrics)
	# ---------------------------------------------------------
	number_cards = [
		{
			"doctype": "Number Card",
			"name": "Total Fleet Vehicles",
			"label": "Total Fleet Vehicles",
			"type": "Document Type",
			"document_type": "Fleet Vehicle",
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
			"document_type": "Fleet Vehicle",
			"function": "Count",
			"filters_json": json.dumps([["Fleet Vehicle", "status", "=", "Available"]]),
			"color": "Green",
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
			"name": "Vehicles Under Maintenance",
			"label": "Vehicles Under Maintenance",
			"type": "Document Type",
			"document_type": "Fleet Vehicle",
			"function": "Count",
			"filters_json": json.dumps([["Fleet Vehicle", "status", "=", "Under Maintenance"]]),
			"color": "Red",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Number Card",
			"name": "Maintenance Due Vehicles",
			"label": "Maintenance Due Vehicles",
			"type": "Document Type",
			"document_type": "Fleet Vehicle",
			"function": "Count",
			"filters_json": json.dumps([["Fleet Vehicle", "status", "=", "Maintenance Due"]]),
			"color": "Yellow",
			"is_public": 1,
			"module": "Fleet Management",
		},
		{
			"doctype": "Number Card",
			"name": "Fuel Locked Vehicles",
			"label": "Fuel Locked Vehicles",
			"type": "Document Type",
			"document_type": "Fleet Vehicle",
			"function": "Count",
			"filters_json": json.dumps([["Fleet Vehicle", "status", "=", "Fuel Locked"]]),
			"color": "Red",
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
			"name": "Total Maintenance Spend",
			"label": "Total Maintenance Spend",
			"type": "Document Type",
			"document_type": "Maintenance Entry",
			"function": "Sum",
			"aggregate_function_based_on": "total_cost",
			"filters_json": json.dumps([["Maintenance Entry", "docstatus", "=", 1]]),
			"color": "Purple",
			"is_public": 1,
			"module": "Fleet Management",
		},
	]

	for card_def in number_cards:
		try:
			if frappe.db.exists("Number Card", card_def["name"]):
				frappe.delete_doc("Number Card", card_def["name"], force=True, ignore_permissions=True)
			doc = frappe.get_doc(card_def)
			doc.insert(ignore_permissions=True)
		except Exception:
			pass

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
			"document_type": "Fleet Vehicle",
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
			"document_type": "Fleet Vehicle",
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
			"document_type": "Maintenance Entry",
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
		try:
			if frappe.db.exists("Dashboard Chart", chart_def["name"]):
				frappe.delete_doc("Dashboard Chart", chart_def["name"], force=True, ignore_permissions=True)
			doc = frappe.get_doc(chart_def)
			doc.insert(ignore_permissions=True)
		except Exception:
			pass

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
			{"number_card_name": "Active Assignments", "label": "Active Assignments"},
			{"number_card_name": "Vehicles Under Maintenance", "label": "Under Maintenance"},
			{"number_card_name": "Maintenance Due Vehicles", "label": "Maintenance Due"},
			{"number_card_name": "Fuel Locked Vehicles", "label": "Fuel Locked"},
			{"number_card_name": "Total Fuel Spend", "label": "Total Fuel Spend"},
			{"number_card_name": "Total Maintenance Spend", "label": "Total Maintenance Spend"},
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
			{"label": "Vehicle Activity Log", "link_to": "Vehicle Activity Log", "type": "Report", "color": "Cyan"},
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
			},
			{
				"hidden": 0,
				"is_query_report": 1,
				"label": "Vehicle Activity Log",
				"link_to": "Vehicle Activity Log",
				"link_type": "Report",
				"type": "Link"
			}
		],
		"content": json.dumps([
			{"type": "header", "data": {"text": "Fleet Analytics & Executive KPI Dashboard", "level": 2}},
			{"type": "number_card", "data": {"number_card_name": "Total Fleet Vehicles"}},
			{"type": "number_card", "data": {"number_card_name": "Available Vehicles"}},
			{"type": "number_card", "data": {"number_card_name": "Active Assignments"}},
			{"type": "number_card", "data": {"number_card_name": "Vehicles Under Maintenance"}},
			{"type": "number_card", "data": {"number_card_name": "Maintenance Due Vehicles"}},
			{"type": "number_card", "data": {"number_card_name": "Fuel Locked Vehicles"}},
			{"type": "number_card", "data": {"number_card_name": "Total Fuel Spend"}},
			{"type": "number_card", "data": {"number_card_name": "Total Maintenance Spend"}},
			{"type": "header", "data": {"text": "Fleet Visual Analytics & Charts", "level": 3}},
			{"type": "chart", "data": {"chart_name": "Fleet Vehicle Status Distribution"}},
			{"type": "chart", "data": {"chart_name": "Vehicle Category Breakdown"}},
			{"type": "chart", "data": {"chart_name": "Monthly Fuel Expense"}},
			{"type": "chart", "data": {"chart_name": "Maintenance Spend Trend"}},
			{"type": "header", "data": {"text": "Reports & Analytics", "level": 3}},
			{"type": "card", "data": {"card_name": "📊 Executive Fleet Reports"}}
		])
	}

	try:
		dash_path = frappe.get_app_path("fleet_management", "fleet_management", "workspace", "fleet_dashboard", "fleet_dashboard.json")
		if os.path.exists(dash_path):
			with open(dash_path, "r", encoding="utf-8") as f:
				dash_data = json.load(f)
			if frappe.db.exists("Workspace", "Fleet Dashboard"):
				frappe.db.delete("Workspace Link", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace Shortcut", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace Number Card", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace Chart", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace", {"name": "Fleet Dashboard"})
			doc = frappe.get_doc(dash_data)
			doc.insert(ignore_permissions=True)
		else:
			if frappe.db.exists("Workspace", "Fleet Dashboard"):
				frappe.db.delete("Workspace Link", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace Shortcut", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace Number Card", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace Chart", {"parent": "Fleet Dashboard"})
				frappe.db.delete("Workspace", {"name": "Fleet Dashboard"})
			doc = frappe.get_doc(dash_workspace)
			doc.insert(ignore_permissions=True)
	except Exception as e:
		print(f"Error syncing Fleet Dashboard Workspace: {e}")

	# ---------------------------------------------------------
	# 4. Sync "Fleet Management" Workspace from JSON
	# ---------------------------------------------------------
	try:
		workspace_path = frappe.get_app_path("fleet_management", "fleet_management", "workspace", "fleet_management", "fleet_management.json")
		if os.path.exists(workspace_path):
			with open(workspace_path, "r", encoding="utf-8") as f:
				fm_data = json.load(f)
			
			if frappe.db.exists("Workspace", "Fleet Management"):
				frappe.db.delete("Workspace Link", {"parent": "Fleet Management"})
				frappe.db.delete("Workspace Shortcut", {"parent": "Fleet Management"})
				frappe.db.delete("Workspace", {"name": "Fleet Management"})
			
			doc = frappe.get_doc(fm_data)
			doc.insert(ignore_permissions=True)
	except Exception as e:
		print(f"Error syncing Fleet Management Workspace: {e}")

	frappe.db.commit()
	print("Fleet Dashboard Workspace, Charts, Number Cards & Workspace Links initialized successfully!")


if __name__ == "__main__":
	setup_fleet_dashboards()
