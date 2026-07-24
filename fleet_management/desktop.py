from frappe import _

def get_data():
	return [
		{
			"module_name": "Fleet Management",
			"type": "module",
			"label": _("Fleet Management"),
			"icon": "octicon octicon-package",
			"color": "#1F2937",
			"category": "Modules",
			"description": _("Enterprise Fleet Management System")
		}
	]
