app_name = "endersuite"
app_title = "EnderSuite"
app_publisher = "RenderCores.com"
app_description = "ERP SaaS Based Software"
app_email = "hola@rendercores.online"
app_license = "gpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "endersuite",
# 		"logo": "/assets/endersuite/logo.png",
# 		"title": "EnderSuite",
# 		"route": "/endersuite",
# 		"has_permission": "endersuite.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/endersuite/css/endersuite.css"
# app_include_js = "/assets/endersuite/js/endersuite.js"

# include js, css files in header of web template
# web_include_css = "/assets/endersuite/css/endersuite.css"
# web_include_js = "/assets/endersuite/js/endersuite.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "endersuite/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "endersuite/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "endersuite.utils.jinja_methods",
# 	"filters": "endersuite.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "endersuite.install.before_install"
after_install = "endersuite.install.after_install"
setup_wizard_complete = "endersuite.install.setup_wizard_complete"
setup_wizard_requires = "assets/endersuite/js/setup_wizard.js"

# Uninstallation
# ------------

# before_uninstall = "endersuite.uninstall.before_uninstall"
# after_uninstall = "endersuite.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "endersuite.utils.before_app_install"
# after_app_install = "endersuite.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "endersuite.utils.before_app_uninstall"
# after_app_uninstall = "endersuite.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "endersuite.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Nota de Venta": {
		"on_submit": "endersuite.ventas.services.stock_service.decrement_stock",
		"on_cancel": "endersuite.ventas.services.stock_service.revert_stock"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"endersuite.contabilidad.fiscal_utils.ensure_current_fiscal_year_daily"
	]
}

# Testing
# -------

# before_tests = "endersuite.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "endersuite.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "endersuite.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["endersuite.utils.before_request"]
# after_request = ["endersuite.utils.after_request"]

# Job Events
# ----------
# before_job = ["endersuite.utils.before_job"]
# after_job = ["endersuite.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"endersuite.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

