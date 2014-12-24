frappe.pages['dashboard-page'].onload = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard-Page',
		single_column: true
	});
	frappe.set_route("Form", 'Work Management', 'Work Management');
}