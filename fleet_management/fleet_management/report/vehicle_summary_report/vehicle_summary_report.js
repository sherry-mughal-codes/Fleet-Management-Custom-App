frappe.query_reports["Vehicle Summary Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Fleet Company"),
			"fieldtype": "Link",
			"options": "Fleet Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nDraft\nAvailable\nReserved\nAssigned\nMaintenance Due\nUnder Maintenance\nInspection\nOut of Service\nInactive\nSold\nScrapped\nArchived"
		},
		{
			"fieldname": "vehicle_brand",
			"label": __("Vehicle Brand"),
			"fieldtype": "Link",
			"options": "Vehicle Brand"
		},
		{
			"fieldname": "vehicle_category",
			"label": __("Vehicle Category"),
			"fieldtype": "Link",
			"options": "Vehicle Category"
		},
		{
			"fieldname": "fuel_type",
			"label": __("Fuel Type"),
			"fieldtype": "Link",
			"options": "Fuel Type"
		}
	]
};
