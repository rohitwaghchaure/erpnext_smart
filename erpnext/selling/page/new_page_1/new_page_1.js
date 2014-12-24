frappe.pages['new-page-1'].onload = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Item Catlog',
		single_column: true
	});
}