frappe.query_reports["Maintenance Summary Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Fleet Company"),
			"fieldtype": "Link",
			"options": "Fleet Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "vehicle",
			"label": __("Vehicle"),
			"fieldtype": "Link",
			"options": "Fleet Vehicle"
		},
		{
			"fieldname": "maintenance_type",
			"label": __("Item / Activity Name"),
			"fieldtype": "Data"
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
