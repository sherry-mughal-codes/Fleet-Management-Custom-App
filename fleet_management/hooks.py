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
# app_include_js = ["/assets/fleet_management/js/fleet_management.js"]

# DocType JS Hooks
doctype_js = {
	"Fleet Settings": "public/js/fleet_settings.js"
}

# Document Events Hooks
# ---------------------
doc_events = {
	"*": {
		"on_update": "fleet_management.permissions.audit.audit_document_change",
	}
}

# Migration Hook
after_migrate = "fleet_management.fleet_management.setup_dashboard.setup_fleet_dashboards"


# Scheduled Tasks
# ---------------
scheduler_events = {
	"all": [
		"fleet_management.services.scheduler.scheduled_health_check"
	],
	"daily": [
		"fleet_management.services.scheduler.scheduled_maintenance_check",
		"fleet_management.services.scheduler.scheduled_fuel_anomaly_check",
		"fleet_management.services.scheduler.scheduled_assignment_expiry_check",
		"fleet_management.services.scheduler.scheduled_fleet_automation_daily"
	],
	"hourly": [
		"fleet_management.services.scheduler.scheduled_maintenance_check"
	],
	"weekly": [
		"fleet_management.services.scheduler.scheduled_cost_refresh",
		"fleet_management.services.scheduler.scheduled_health_check"
	],
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
		"filters": [["module", "=", "Fleet Management"]]
	},
	{
		"dt": "Number Card",
		"filters": [["module", "=", "Fleet Management"]]
	},
	{
		"dt": "Dashboard Chart",
		"filters": [["module", "=", "Fleet Management"]]
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
	},
	{
		"dt": "Company",
		"filters": [["name", "is", "set"]]
	}
]


