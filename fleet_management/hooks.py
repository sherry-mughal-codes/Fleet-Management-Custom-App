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

# include js, css files in header of web template
# web_include_css = "/assets/fleet_management/css/fleet_management.css"
# web_include_js = "/assets/fleet_management/js/fleet_management.js"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# Permissions
# -----------
# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class Overrides
# -----------------------
# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# doc_events = {
# 	"*": {
# 		"on_update": "fleet_management.permissions.audit.audit_document_change",
# 	}
# }

# Scheduled Tasks
# ---------------
# scheduler_events = {
# 	"all": [
# 		"fleet_management.services.base_service.scheduled_health_check"
# 	],
# 	"daily": [],
# 	"hourly": [],
# 	"weekly": [],
# 	"monthly": [],
# }

# Testing
# -------
# before_tests = "fleet_management.tests.conftest.before_tests"

# Boot Session
# ------------
# boot_session = "fleet_management.api.base.boot_session"

# Fixtures
# --------
fixtures = [
	{
		"dt": "Workspace",
		"filters": [["name", "=", "Fleet Management"]]
	}
]
