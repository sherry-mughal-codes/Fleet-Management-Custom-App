frappe.query_reports["Fleet Cost Summary Report"] = {
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
