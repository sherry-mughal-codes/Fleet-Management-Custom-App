import frappe


def execute():
	"""
	Database Migration Patch:
	Safely renames custom DocType 'Vehicle' to 'Fleet Vehicle' if 'Vehicle' DocType exists.
	Preserves all existing vehicle records in database without data loss.
	"""
	if frappe.db.exists("DocType", "Vehicle") and not frappe.db.exists("DocType", "Fleet Vehicle"):
		frappe.rename_doc("DocType", "Vehicle", "Fleet Vehicle", force=True)
		frappe.db.commit()
