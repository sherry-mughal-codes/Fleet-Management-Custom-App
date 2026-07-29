"""
Vehicle Activity Log Script Report
Fleet Management System (Frappe v15)

Generates a unified chronological activity log for vehicles across:
- Vehicle registration / creation
- Vehicle Assignments (Handover & Return)
- Fuel Entries
- Maintenance Entries
"""

from typing import Any, Dict, List, Tuple
import frappe
from frappe import _


def execute(filters: Dict[str, Any] | None = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns() -> List[Dict[str, Any]]:
	return [
		{
			"fieldname": "activity_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"fieldname": "vehicle",
			"label": _("Vehicle"),
			"fieldtype": "Link",
			"options": "Vehicle",
			"width": 150,
		},
		{
			"fieldname": "activity_type",
			"label": _("Activity Type"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "employee",
			"label": _("Driver / Employee"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "start_odometer",
			"label": _("Start Odometer (KM)"),
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"fieldname": "end_odometer",
			"label": _("End Odometer (KM)"),
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"fieldname": "distance_travelled",
			"label": _("Distance (KM)"),
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"fieldname": "total_cost",
			"label": _("Total Cost"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "details",
			"label": _("Details / Remarks"),
			"fieldtype": "Data",
			"width": 260,
		},
		{
			"fieldname": "ref_doctype",
			"label": _("Reference DocType"),
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "ref_docname",
			"label": _("Reference Document"),
			"fieldtype": "Dynamic Link",
			"options": "ref_doctype",
			"width": 180,
		},
	]


def get_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
	if not hasattr(frappe, "db") or not frappe.db:
		return []

	vehicle_filter = filters.get("vehicle")
	company_filter = filters.get("company")
	activity_type_filter = filters.get("activity_type")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	events = []

	# 1. Vehicle Registration Events
	v_conditions = []
	v_args = []
	if vehicle_filter:
		v_conditions.append("name = %s")
		v_args.append(vehicle_filter)
	if company_filter:
		v_conditions.append("company = %s")
		v_args.append(company_filter)

	v_where = (" WHERE " + " AND ".join(v_conditions)) if v_conditions else ""
	try:
		vehicles = frappe.db.sql(f"""
			SELECT name, vehicle_number, company, creation, initial_odometer, current_odometer
			FROM `tabVehicle`
			{v_where}
		""", tuple(v_args), as_dict=True)

		for v in vehicles:
			reg_date = str(v.creation)[:10] if v.creation else None
			if from_date and reg_date and reg_date < str(from_date):
				continue
			if to_date and reg_date and reg_date > str(to_date):
				continue

			if not activity_type_filter or activity_type_filter in ("All", "Vehicle Creation"):
				events.append({
					"activity_date": reg_date,
					"vehicle": v.name,
					"activity_type": "Vehicle Creation",
					"employee": None,
					"start_odometer": 0.0,
					"end_odometer": float(v.initial_odometer or 0.0),
					"distance_travelled": 0.0,
					"total_cost": 0.0,
					"details": f"Vehicle Registered with Initial Odometer: {v.initial_odometer or 0} KM",
					"ref_doctype": "Vehicle",
					"ref_docname": v.name
				})
	except Exception:
		pass

	# 2. Vehicle Assignments (Handover & Return)
	asn_conditions = []
	asn_args = []
	if vehicle_filter:
		asn_conditions.append("vehicle = %s")
		asn_args.append(vehicle_filter)
	if company_filter:
		asn_conditions.append("company = %s")
		asn_args.append(company_filter)

	asn_where = (" WHERE " + " AND ".join(asn_conditions)) if asn_conditions else ""
	try:
		assignments = frappe.db.sql(f"""
			SELECT name, vehicle, employee, company, assignment_date, return_date, opening_odometer, closing_odometer, status
			FROM `tabVehicle Assignment`
			{asn_where}
		""", tuple(asn_args), as_dict=True)

		for a in assignments:
			# Handover event
			h_date = str(a.assignment_date) if a.assignment_date else None
			if h_date and (not from_date or h_date >= str(from_date)) and (not to_date or h_date <= str(to_date)):
				if not activity_type_filter or activity_type_filter in ("All", "Assignment Handover"):
					events.append({
						"activity_date": h_date,
						"vehicle": a.vehicle,
						"activity_type": "Assignment Handover",
						"employee": a.employee,
						"start_odometer": float(a.opening_odometer or 0.0),
						"end_odometer": float(a.opening_odometer or 0.0),
						"distance_travelled": 0.0,
						"total_cost": 0.0,
						"details": f"Vehicle Handed Over to Driver {a.employee or '---'} at {a.opening_odometer or 0} KM",
						"ref_doctype": "Vehicle Assignment",
						"ref_docname": a.name
					})

			# Return event
			if a.return_date:
				r_date = str(a.return_date)
				if (not from_date or r_date >= str(from_date)) and (not to_date or r_date <= str(to_date)):
					if not activity_type_filter or activity_type_filter in ("All", "Assignment Return"):
						start_o = float(a.opening_odometer or 0.0)
						end_o = float(a.closing_odometer or start_o)
						dist = max(0.0, end_o - start_o)
						events.append({
							"activity_date": r_date,
							"vehicle": a.vehicle,
							"activity_type": "Assignment Return",
							"employee": a.employee,
							"start_odometer": start_o,
							"end_odometer": end_o,
							"distance_travelled": dist,
							"total_cost": 0.0,
							"details": f"Vehicle Returned by Driver {a.employee or '---'} (Distance: {dist} KM)",
							"ref_doctype": "Vehicle Assignment",
							"ref_docname": a.name
						})
	except Exception:
		pass

	# 3. Fuel Entries
	fuel_conditions = ["docstatus = 1"]
	fuel_args = []
	if vehicle_filter:
		fuel_conditions.append("vehicle = %s")
		fuel_args.append(vehicle_filter)
	if company_filter:
		fuel_conditions.append("company = %s")
		fuel_args.append(company_filter)

	fuel_where = " WHERE " + " AND ".join(fuel_conditions)
	try:
		fuels = frappe.db.sql(f"""
			SELECT name, vehicle, employee, fuel_date, odometer, previous_odometer, distance_travelled, fuel_qty, total_cost
			FROM `tabFuel Entry`
			{fuel_where}
		""", tuple(fuel_args), as_dict=True)

		for f in fuels:
			f_date = str(f.fuel_date) if f.fuel_date else None
			if f_date and (not from_date or f_date >= str(from_date)) and (not to_date or f_date <= str(to_date)):
				if not activity_type_filter or activity_type_filter in ("All", "Fuel Entry"):
					p_odo = float(f.previous_odometer or 0.0)
					c_odo = float(f.odometer or 0.0)
					dist = float(f.distance_travelled or max(0.0, c_odo - p_odo))
					qty = float(f.fuel_qty or 0.0)
					cost = float(f.total_cost or 0.0)
					events.append({
						"activity_date": f_date,
						"vehicle": f.vehicle,
						"activity_type": "Fuel Entry",
						"employee": f.employee,
						"start_odometer": p_odo,
						"end_odometer": c_odo,
						"distance_travelled": dist,
						"total_cost": cost,
						"details": f"Refilled {qty} L Fuel at {c_odo} KM (Cost: PKR {cost})",
						"ref_doctype": "Fuel Entry",
						"ref_docname": f.name
					})
	except Exception:
		pass

	# 4. Maintenance Entries
	maint_conditions = ["docstatus = 1"]
	maint_args = []
	if vehicle_filter:
		maint_conditions.append("vehicle = %s")
		maint_args.append(vehicle_filter)
	if company_filter:
		maint_conditions.append("company = %s")
		maint_args.append(company_filter)

	maint_where = " WHERE " + " AND ".join(maint_conditions)
	try:
		maints = frappe.db.sql(f"""
			SELECT me.name, me.vehicle, me.maintenance_date, me.current_odometer, me.total_cost, me.maintenance_type, va.employee
			FROM `tabMaintenance Entry` me
			LEFT JOIN `tabVehicle Assignment` va ON me.assignment = va.name
			{maint_where}
		""", tuple(maint_args), as_dict=True)

		for m in maints:
			m_date = str(m.maintenance_date) if m.maintenance_date else None
			if m_date and (not from_date or m_date >= str(from_date)) and (not to_date or m_date <= str(to_date)):
				if not activity_type_filter or activity_type_filter in ("All", "Maintenance Entry"):
					c_odo = float(m.current_odometer or 0.0)
					cost = float(m.total_cost or 0.0)
					m_desc = m.maintenance_type or "General Servicing"
					events.append({
						"activity_date": m_date,
						"vehicle": m.vehicle,
						"activity_type": "Maintenance Entry",
						"employee": m.employee,
						"start_odometer": c_odo,
						"end_odometer": c_odo,
						"distance_travelled": 0.0,
						"total_cost": cost,
						"details": f"Serviced: {m_desc} at {c_odo} KM (Cost: PKR {cost})",
						"ref_doctype": "Maintenance Entry",
						"ref_docname": m.name
					})
	except Exception:
		pass

	events.sort(key=lambda x: (x.get("activity_date") or "", x.get("end_odometer") or 0.0), reverse=True)
	return events
