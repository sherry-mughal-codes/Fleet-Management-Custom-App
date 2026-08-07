frappe.query_reports["Vehicle Activity Log"] = {
	"filters": [
		{
			"fieldname": "vehicle",
			"label": __("Vehicle"),
			"fieldtype": "Link",
			"options": "Fleet Vehicle"
		},
		{
			"fieldname": "company",
			"label": __("Fleet Company"),
			"fieldtype": "Link",
			"options": "Fleet Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "employee",
			"label": __("Assigned User / Driver"),
			"fieldtype": "Link",
			"options": "User"
		},
		{
			"fieldname": "activity_type",
			"label": __("Activity Type"),
			"fieldtype": "Select",
			"options": "\nAll\nVehicle Creation\nAssignment Handover\nAssignment Return\nFuel Entry\nMaintenance Entry"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		}
	]
};
