frappe.pages['new-page'].onload = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Item Catlog',
		single_column: true
	});
}