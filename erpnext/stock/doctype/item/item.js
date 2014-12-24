// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.item");

cur_frm.cscript.refresh = function(doc) {
	// make sensitive fields(has_serial_no, is_stock_item, valuation_method)
	// read only if any stock ledger entry exists

	cur_frm.cscript.make_dashboard();

	if (frappe.defaults.get_default("item_naming_by")!="Naming Series") {
		cur_frm.toggle_display("naming_series", false);
	} else {
		erpnext.toggle_naming_series();
	}


	cur_frm.cscript.edit_prices_button();

	if (!doc.__islocal && doc.is_stock_item == 'Yes') {
		cur_frm.toggle_enable(['has_serial_no', 'is_stock_item', 'valuation_method'],
			(doc.__onload && doc.__onload.sle_exists=="exists") ? false : true);
	}

	if (!doc.__islocal && doc.show_in_website) {
		cur_frm.set_intro(__("Published on website at: {0}",
			[repl('<a href="/%(website_route)s" target="_blank">/%(website_route)s</a>', doc.__onload)]));
	}

	erpnext.item.toggle_reqd(cur_frm);
	
}

erpnext.item.toggle_reqd = function(frm) {
	frm.toggle_reqd("default_warehouse", frm.doc.is_stock_item==="Yes");
};

frappe.ui.form.on("Item", "is_stock_item", function(frm) {
	erpnext.item.toggle_reqd(frm);
});


cur_frm.cscript.make_dashboard = function() {
	cur_frm.dashboard.reset();
	if(cur_frm.doc.__islocal)
		return;
}

cur_frm.cscript.edit_prices_button = function() {
	cur_frm.add_custom_button("Add / Edit Prices", function() {
		frappe.set_route("Report", "Item Price", {"item_code": cur_frm.doc.name});
	}, "icon-money");
}

cur_frm.cscript.item_code = function(doc) {
	if(!doc.item_name)
		cur_frm.set_value("item_name", doc.item_code);
	if(!doc.description)
		cur_frm.set_value("description", doc.item_code);
}

cur_frm.fields_dict['default_bom'].get_query = function(doc) {
	return {
		filters: {
			'item': doc.item_code,
			'is_active': 0
		}
	}
}


// Expense Account
// ---------------------------------
cur_frm.fields_dict['expense_account'].get_query = function(doc) {
	return {
		filters: {
			"report_type": "Profit and Loss",
			"group_or_ledger": "Ledger"
		}
	}
}

// Income Account
// --------------------------------
cur_frm.fields_dict['income_account'].get_query = function(doc) {
	return {
		filters: {
			"report_type": "Profit and Loss",
			'group_or_ledger': "Ledger",
			'account_type': "Income Account"
		}
	}
}


// Purchase Cost Center
// -----------------------------
cur_frm.fields_dict['buying_cost_center'].get_query = function(doc) {
	return {
		filters:{ 'group_or_ledger': "Ledger" }
	}
}


// Sales Cost Center
// -----------------------------
cur_frm.fields_dict['selling_cost_center'].get_query = function(doc) {
	return {
		filters:{ 'group_or_ledger': "Ledger" }
	}
}


cur_frm.fields_dict['item_tax'].grid.get_field("tax_type").get_query = function(doc, cdt, cdn) {
	return {
		filters: [
			['Account', 'account_type', 'in',
				'Tax, Chargeable, Income Account, Expense Account'],
			['Account', 'docstatus', '!=', 2]
		]
	}
}

cur_frm.cscript.tax_type = function(doc, cdt, cdn){
	var d = locals[cdt][cdn];
	return get_server_fields('get_tax_rate', d.tax_type, 'item_tax', doc, cdt, cdn, 1);
}

cur_frm.fields_dict['item_group'].get_query = function(doc,cdt,cdn) {
	return {
		filters: [
			['Item Group', 'docstatus', '!=', 2]
		]
	}
}

cur_frm.cscript.add_image = function(doc, dt, dn) {
	if(!doc.image) {
		msgprint(__('Please select an "Image" first'));
		return;
	}

	doc.description_html = repl('<table style="width: 100%; table-layout: fixed;">' +
		'<tr><td style="width:110px"><img src="%(imgurl)s" width="100px"></td>' +
		'<td>%(desc)s</td></tr>' +
		'</table>', {imgurl: frappe.utils.get_file_link(doc.image), desc:doc.description});

	refresh_field('description_html');
}

// Quotation to validation - either customer or lead mandatory
cur_frm.cscript.weight_to_validate = function(doc, cdt, cdn){
	if((doc.nett_weight || doc.gross_weight) && !doc.weight_uom) {
		msgprint(__('Weight is mentioned,\nPlease mention "Weight UOM" too'));
		validated = 0;
	}
}

cur_frm.cscript.validate = function(doc, cdt, cdn){
	cur_frm.cscript.weight_to_validate(doc, cdt, cdn);
	setTimeout(function(){refresh_field('barcode_image');},1000)
}

cur_frm.fields_dict.item_customer_details.grid.get_field("customer_name").get_query = function(doc, cdt, cdn) {
	return { query: "erpnext.controllers.queries.customer_query" }
}

cur_frm.fields_dict.item_supplier_details.grid.get_field("supplier").get_query = function(doc, cdt, cdn) {
	return { query: "erpnext.controllers.queries.supplier_query" }
}

cur_frm.cscript.copy_from_item_group = function(doc) {
	return cur_frm.call({
		doc: doc,
		method: "copy_specification_from_item_group"
	});
}

// cur_frm.cscript.image = function() {
// 	refresh_field("image_view");

// 	if(!cur_frm.doc.image) return;

// 	if(!cur_frm.doc.description_html)
// 		cur_frm.cscript.add_image(cur_frm.doc);
// 	else {
// 		msgprint(__("You may need to update: {0}", [frappe.meta.get_docfield(cur_frm.doc.doctype, "description_html").label]));
// 	}
// }
//Rohit
cur_frm.cscript.image = function(doc, cdt, cdn) {
var d = locals[cdt][cdn]
d.image_view = '<table style="width: 100%; table-layout: fixed;"><tr><td><img src="'+d.image+'" width="100px"></td></tr></table>'
refresh_field("measurement_item");
}
cur_frm.cscript.add_image = function(doc, cdt, cdn) {
var d = locals[cdt][cdn]
d.image_viewer = '<table style="width: 100%; table-layout: fixed;"><tr><td ><img src="'+d.add_image+'" width="100px"></td></tr></table>'
refresh_field("style_item");
}
cur_frm.cscript.measurement_template = function(doc, cdt, cdn){
get_server_fields('get_measurement_details',doc.measurement_template,'',doc ,cdt, cdn,1, function(){
refresh_field('measurement_item')
})
}
cur_frm.cscript.style = function(doc, cdt, cdn){
var	d = locals[cdt][cdn]
get_server_fields('get_style_details',d.style,'',doc ,cdt, cdn,1, function(){
refresh_field('style_item')
})
}
// cur_frm.cscript.onload= function(doc, cdt, cdn) {
// 	alert("hii")
// return get_server_fields('get_details','', '', doc, cdt, cdn, 1,function(){
// refresh_field('size_item')
// });
// };

cur_frm.cscript.item_group =function(doc, cdt, cdn){
	if(doc.item_group == 'Tailoring'){
		doc.has_serial_no = 'Yes'
		refresh_field('has_serial_no')
	}
}


//for Slide Show

cur_frm.add_fetch('default_branch', 'warehouse', 'default_warehouse')
{% include 'stock/custom_items.js' %}
cur_frm.script_manager.make(erpnext.stock.CustomItem);


cur_frm.fields_dict.item_specification_details.grid.get_field("qi_process").get_query = function(doc, cdt, cdn) {
		var d = locals[cdt][cdn]
		get_list = cur_frm.cscript.get_list(doc, cdt, cdn)
      	return {
      		query : "tools.tools_management.custom_methods.get_process_details",
      		filters : {
      			'obj':JSON.stringify(get_list),
      		}
      	}
}

cur_frm.cscript.get_list= function(doc, cdt, cdn){
	var cl = doc.process_item || [ ]
	data = []
	$.each(cl, function(i){
		if(parseInt(cl[i].quality_check)==1 || parseInt(cl[i].trials_qc)==1){
			data.push(cl[i].process_name)
		}
	})
	return data
}

// cur_frm.cscript.onload_post_render = function() {
// 	frappe.require('assets/frappe/js/lib/jscolor/jscolor.js');
// 	$.each(["fabric_color"], function(i, v) {
// 		$(cur_frm.fields_dict[v].input).addClass('color');
// 	})
// 	jscolor.bind();
// }