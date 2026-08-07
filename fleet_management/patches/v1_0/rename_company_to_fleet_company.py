import frappe


def execute():
	"""
	Safely renames custom DocType 'Company' to 'Fleet Company' if 'Company' DocType exists.
	Renames DB table tabCompany -> tabFleet Company and updates parenttype references.
	"""
	if frappe.db.exists("DocType", "Company") and not frappe.db.exists("DocType", "Fleet Company"):
		frappe.rename_doc("DocType", "Company", "Fleet Company", force=True)
