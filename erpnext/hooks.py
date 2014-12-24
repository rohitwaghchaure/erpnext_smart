app_name = "erpnext"
app_title = "ERPNext"
app_publisher = "Web Notes Technologies Pvt. Ltd. and Contributors"
app_description = "Open Source Enterprise Resource Planning for Small and Midsized Organizations"
app_icon = "icon-th"
app_color = "#e74c3c"
app_version = "4.3.0"

error_report_email = "support@erpnext.com"

app_include_js = ["assets/js/erpnext.min.js"
					]
app_include_css = ["assets/css/erpnext.css"
					]
web_include_js = "assets/js/erpnext-web.min.js"

after_install = "erpnext.setup.install.after_install"

boot_session = "erpnext.startup.boot.boot_session"
notification_config = "erpnext.startup.notifications.get_notification_config"

dump_report_map = "erpnext.startup.report_data_map.data_map"
update_website_context = "erpnext.startup.webutils.update_website_context"

on_session_creation = "erpnext.startup.event_handlers.on_session_creation"
before_tests = "erpnext.setup.utils.before_tests"

website_generators = ["Item Group", "Item", "Sales Partner"]

standard_queries = "Customer:erpnext.selling.doctype.customer.customer.get_customer_list"

permission_query_conditions = {
		"Feed": "erpnext.home.doctype.feed.feed.get_permission_query_conditions",
		"Note": "erpnext.utilities.doctype.note.note.get_permission_query_conditions"
	}

has_permission = {
		"Feed": "erpnext.home.doctype.feed.feed.has_permission",
		"Note": "erpnext.utilities.doctype.note.note.has_permission"
	}


doc_events = {
	"*": {
		"on_update": "erpnext.home.update_feed",
		"on_submit": "erpnext.home.update_feed"
	},
	"Comment": {
		"on_update": "erpnext.home.make_comment_feed"
	},
	"Stock Entry": {
		"on_submit": ["erpnext.stock.doctype.material_request.material_request.update_completed_qty","erpnext.stock.stock_custom_methods.stock_out_entry","erpnext.stock.stock_custom_methods.in_stock_entry"],
		"on_cancel": "erpnext.stock.doctype.material_request.material_request.update_completed_qty"
	},
	"User": {
		"validate": "erpnext.hr.doctype.employee.employee.validate_employee_role",
		"on_update": "erpnext.hr.doctype.employee.employee.update_user_permissions"
	},
	"User": {
		"validate": [
		"erpnext.hr.doctype.employee.employee.validate_employee_role",
		"erpnext.setup.doctype.site_master.site_master.validate_validity",
		"erpnext.stock.stock_custom_methods.update_user_permissions_for_user"
		],
		"on_update":[ 
		"erpnext.hr.doctype.employee.employee.update_user_permissions",
		"erpnext.setup.doctype.site_master.site_master.update_users"
		],
	},
	"Branch": {
		"validate" : "tools.tools_management.custom_methods.branch_methods"

	},
	"Sales Invoice": {
		"on_update" : ["erpnext.accounts.accounts_custom_methods.add_data_in_work_order_assignment", "erpnext.accounts.accounts_custom_methods.create_serial_no"],#"tools.tools_management.custom_methods.update_work_order","tools.tools_management.custom_methods.create_se_or_mr"],
		"validate"  : ["tools.tools_management.custom_methods.merge_tailoring_items", "erpnext.accounts.accounts_custom_methods.invoice_validation_method"], 
		"on_submit" : ["tools.tools_management.custom_methods.sales_invoice_on_submit_methods","erpnext.accounts.accounts_custom_methods.create_production_process","erpnext.accounts.accounts_custom_methods.validate_sales_invoice","tools.tools_management.custom_methods.create_se_or_mr", "mreq.mreq.page.sales_dashboard.sales_dashboard.create_swatch_item_po"],
		"on_cancel" : ["tools.tools_management.custom_methods.delete_project_aginst_si", "erpnext.accounts.accounts_custom_methods.delete_production_process"]
	},
	"Item":{
		"validate" : "erpnext.stock.stock_custom_methods.make_barcode",
		"on_update": "erpnext.stock.stock_custom_methods.item_validate_methods"

	},
	"Employee":{
		"validate": "erpnext.stock.stock_custom_methods.update_user_permissions_for_emp"
	},
	"Quality Inspection":{
		"on_update" : "erpnext.accounts.accounts_custom_methods.update_QI_status",
		"on_submit" : "erpnext.accounts.accounts_custom_methods.make_stock_entry_against_qc"
	}
}

scheduler_events = {
	"all": [
		"erpnext.support.doctype.support_ticket.get_support_mails.get_support_mails",
		"erpnext.hr.doctype.job_applicant.get_job_applications.get_job_applications",
		"erpnext.selling.doctype.lead.get_leads.get_leads",
		"erpnext.setup.doctype.site_master.site_master.create_support",
		"erpnext.setup.doctype.site_master.site_master.create_feedback",
		"erpnext.setup.doctype.site_master.site_master.assign_support",
		"erpnext.setup.doctype.site_master.site_master.disable_user",
		"erpnext.setup.doctype.site_master.site_master.add_validity",
	],
	"daily": [
		"erpnext.controllers.recurring_document.create_recurring_documents",
		"erpnext.stock.utils.reorder_item",
		"erpnext.setup.doctype.email_digest.email_digest.send",
		"erpnext.support.doctype.support_ticket.support_ticket.auto_close_tickets"
	],
	"daily_long": [
		"erpnext.setup.doctype.backup_manager.backup_manager.take_backups_daily"
	],
	"weekly_long": [
		"erpnext.setup.doctype.backup_manager.backup_manager.take_backups_weekly"
	]
}

