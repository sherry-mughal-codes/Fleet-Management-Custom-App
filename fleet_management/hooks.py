"""
Fleet Management Hooks Configuration
Frappe Framework v15
"""

app_name = "fleet_management"
app_title = "Fleet Management"
app_publisher = "Fleet Management Team"
app_description = "Production-Grade Enterprise Fleet Management System for Frappe Framework v15"
app_email = "developer@fleetmanagement.local"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/fleet_management/css/fleet_management.css"
# app_include_js = "/assets/fleet_management/js/fleet_management.js"

# Document Events Hooks
# ---------------------
doc_events = {
	"*": {
		"on_update": "fleet_management.permissions.audit.audit_document_change",
	}
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"all": [
		"fleet_management.services.base_service.scheduled_health_check"
	],
	"daily": [],
	"hourly": [],
	"weekly": [],
	"monthly": [],
}

# Boot Session
# ------------
boot_session = "fleet_management.api.base.boot_session"

# Fixtures Export Declarations
# ----------------------------
fixtures = [
	{
		"dt": "Workspace",
		"filters": [["name", "=", "Fleet Management"]]
	},
	{
		"dt": "Vehicle Category",
		"filters": [["is_active", "=", 1]]
	},
	{
		"dt": "Fuel Type",
		"filters": [["is_active", "=", 1]]
	},
	{
		"dt": "Maintenance Type",
		"filters": [["is_active", "=", 1]]
	},
	{
		"dt": "Expense Category",
		"filters": [["is_active", "=", 1]]
	},
	{
		"dt": "Distance Unit",
		"filters": [["is_active", "=", 1]]
	},
	{
		"dt": "Fuel Unit",
		"filters": [["is_active", "=", 1]]
	}
]
