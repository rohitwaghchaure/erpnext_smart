frappe.pages['report-template'].onload = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Product Catalog',
		single_column: true
	});

	
	$("<div id ='product_catlog' style='width:100%'><table style='width:100%'><tr><td valign='top' id='catlog_structure' style='width:50%;'></td>\
		<td id='image_view' style='width:50%;margin:20px;'></td></tr></div>").appendTo($(wrapper).find(".layout-main"))

	wrapper.appframe.set_title_right('Refresh', function() {
			$('#image_view').html('');
			erpnext.sales_chart = new erpnext.SalesChart('Product Catalog', 'External Product Catalog', $(wrapper).find("#catlog_structure"))
	});
	erpnext.sales_chart = new erpnext.SalesChart('Product Catalog', 'External Product Catalog', $(wrapper).find("#catlog_structure"))
}


erpnext.SalesChart = Class.extend({
	init: function(ctype, root, parent) {
		$(parent).empty();
		var me = this;
		me.ctype = ctype;
		me.can_read = frappe.model.can_read(this.ctype);
		me.can_create = frappe.boot.user.can_create.indexOf(this.ctype) !== -1 ||
					frappe.boot.user.in_create.indexOf(this.ctype) !== -1;
		me.can_write = frappe.model.can_write(this.ctype);
		me.can_delete = frappe.model.can_delete(this.ctype);
		frappe.require("assets/frappe/js/frappe/ui/productcatlog.js");
		this.tree = new frappe.ui.ProductCatlog({
			parent: $(parent),
			label: root,
			args: {ctype: ctype},
			method: 'erpnext.selling.page.sales_browser.sales_browser.get_product_children',
			toolbar: [
				{toggle_btn: true},
				{
					label:__("Edit"),
					condition: function(node) {
						return !node.root && me.can_read && user=='Administrator';
					},
					click: function(node) {
						frappe.set_route("Form", me.ctype, node.label);
					}
				},
				{
					label:__("Add Child"),
					condition: function(node) { return me.can_create && node.expandable && user=='Administrator'; },
					click: function(node) {
						me.new_node();
					}
				},
				{
					label:__("Delete"),
					condition: function(node) { return !node.root && me.can_delete && user=='Administrator'; },
					click: function(node) {
						frappe.model.delete_doc(me.ctype, node.label, function() {
							$('#image_view').html('');
							node.parent.remove();
						});
					}
				}

			]
		});
		me.view_iamge_structure()
	},
	view_iamge_structure:function(){
		var me = this;
		$(this.wrapper).find('.tree-label').click(function(){
			alert($(this).val())
		})
	},
	new_node: function() {
		var me = this;

		var fields = [
			{fieldtype:'Data', fieldname: 'name_field',
				label:'New ' + me.ctype + ' Name', reqd:true},
			{fieldtype:'Attach', fieldname: 'image_upload',
				label:'Upload Image', reqd:true},
			{fieldtype:'Select', fieldname:'is_group', label:'Group Node', options:'No\nYes',
				description: __("Further nodes can be only created under 'Group' type nodes")},
			{fieldtype:'Button', fieldname:'create_new', label:'Create New' }
		]

		if(me.ctype == "Sales Person") {
			fields.splice(-1, 0, {fieldtype:'Link', fieldname:'employee', label:'Employee',
				options:'Employee', description: __("Please enter Employee Id of this sales parson")});
		}

		// the dialog
		var d = new frappe.ui.Dialog({
			title: __('New ') + __(me.ctype),
			fields: fields
		})

		d.set_value("is_group", "No");
		// create
		$(d.fields_dict.create_new.input).click(function() {
			var btn = this;
			var v = d.get_values();
			if(!v) return;

			var node = me.tree.get_selected_node();

			v.parent = node.label;
			v.ctype = me.ctype;
			v.filename = v.image_upload.split(",")[0];
			v.filedata = v.image_upload;

			return frappe.call({
				method: 'erpnext.accounts.page.report_template.report_template.add_node',
				args: v,
				callback: function(r) {
					if(!r.exc) {
						d.hide();
						if(node.expanded) {
							node.toggle_node();
						}
						node.reload();
					}
				}
			});
		});
		d.show();
	},
	view_image: function(name){

		return frappe.call({
				method: 'erpnext.accounts.page.report_template.report_template.view_image',
				args: {'name':name},
				callback: function(r) {
					if(r.message) {
						$('#image_view').html('<img style="border:5px;width:300px; height:250px; solid #E0E0E0" src="'+r.message+'">')	
					}
				}
		});
	}
});
