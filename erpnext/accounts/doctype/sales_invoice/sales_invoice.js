// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.cscript.tname = "Sales Invoice Item";
cur_frm.cscript.fname = "entries";
cur_frm.cscript.other_fname = "other_charges";
cur_frm.cscript.sales_team_fname = "sales_team";

// print heading
cur_frm.pformat.print_heading = 'Invoice';

{% include 'selling/sales_common.js' %};
{% include 'accounts/doctype/sales_taxes_and_charges_master/sales_taxes_and_charges_master.js' %}
{% include 'accounts/doctype/sales_invoice/pos.js' %}

frappe.provide("erpnext.accounts");
erpnext.accounts.SalesInvoiceController = erpnext.selling.SellingController.extend({
	onload: function() {
		this._super();

		if(!this.frm.doc.__islocal && !this.frm.doc.customer && this.frm.doc.debit_to) {
			// show debit_to in print format
			this.frm.set_df_property("debit_to", "print_hide", 0);
		}

		// toggle to pos view if is_pos is 1 in user_defaults
		if ((is_null(this.frm.doc.is_pos) && cint(frappe.defaults.get_user_default("is_pos"))===1) || this.frm.doc.is_pos) {
			if(this.frm.doc.__islocal && !this.frm.doc.amended_from && !this.frm.doc.customer) {
				this.frm.set_value("is_pos", 1);
				this.is_pos(function() {
					if (cint(frappe.defaults.get_user_defaults("fs_pos_view"))===1)
						cur_frm.cscript.toggle_pos(true);
				});
			}
		}

		// if document is POS then change default print format to "POS Invoice" if no default is specified
		if(cur_frm.doc.is_pos && cur_frm.doc.docstatus===1 && cint(frappe.defaults.get_user_defaults("fs_pos_view"))===1
			&& !locals.DocType[cur_frm.doctype].default_print_format) {
			locals.DocType[cur_frm.doctype].default_print_format = "POS Invoice";
			cur_frm.setup_print_layout();
		}
	},

	refresh: function(doc, dt, dn) {
		this._super();

		cur_frm.cscript.is_opening(doc, dt, dn);
		cur_frm.dashboard.reset();

		if(doc.docstatus==1) {
			cur_frm.appframe.add_button('View Ledger', function() {
				frappe.route_options = {
					"voucher_no": doc.name,
					"from_date": doc.posting_date,
					"to_date": doc.posting_date,
					"company": doc.company,
					group_by_voucher: 0
				};
				frappe.set_route("query-report", "General Ledger");
			}, "icon-table");

			var percent_paid = cint(flt(doc.grand_total - doc.outstanding_amount) / flt(doc.grand_total) * 100);
			cur_frm.dashboard.add_progress(percent_paid + "% Paid", percent_paid);

			cur_frm.appframe.add_button(__('Send SMS'), cur_frm.cscript.send_sms, 'icon-mobile-phone');

			if(cint(doc.update_stock)!=1) {
				// show Make Delivery Note button only if Sales Invoice is not created from Delivery Note
				var from_delivery_note = false;
				from_delivery_note = cur_frm.doc.entries
					.some(function(item) {
						return item.delivery_note ? true : false;
					});

				if(!from_delivery_note) {
					cur_frm.appframe.add_primary_action(__('Make Delivery'), cur_frm.cscript['Make Delivery Note'], "icon-truck")
				}
			}

			if(doc.outstanding_amount!=0) {
				cur_frm.appframe.add_primary_action(__('Make Payment Entry'), cur_frm.cscript.make_bank_voucher, "icon-money");
			}
		}

		// Show buttons only when pos view is active
		if (doc.docstatus===0 && !this.pos_active) {
			cur_frm.cscript.sales_order_btn();
			cur_frm.cscript.delivery_note_btn();
		}
	},

	sales_order_btn: function() {
		this.$sales_order_btn = cur_frm.appframe.add_primary_action(__('From Sales Order'),
			function() {
				frappe.model.map_current_doc({
					method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
					source_doctype: "Sales Order",
					get_query_filters: {
						docstatus: 1,
						status: ["!=", "Stopped"],
						per_billed: ["<", 99.99],
						customer: cur_frm.doc.customer || undefined,
						company: cur_frm.doc.company
					}
				})
			}, "icon-download", "btn-default");
	},

	delivery_note_btn: function() {
		this.$delivery_note_btn = cur_frm.appframe.add_primary_action(__('From Delivery Note'),
			function() {
				frappe.model.map_current_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
					source_doctype: "Delivery Note",
					get_query: function() {
						var filters = {
							company: cur_frm.doc.company
						};
						if(cur_frm.doc.customer) filters["customer"] = cur_frm.doc.customer;
						return {
							query: "erpnext.controllers.queries.get_delivery_notes_to_be_billed",
							filters: filters
						};
					}
				});
			}, "icon-download", "btn-default");
	},

	tc_name: function() {
		this.get_terms();
	},

	is_pos: function(doc, dt, dn, callback_fn) {
		cur_frm.cscript.hide_fields(this.frm.doc);
		if(cint(this.frm.doc.is_pos)) {
			if(!this.frm.doc.company) {
				this.frm.set_value("is_pos", 0);
				msgprint(__("Please specify Company to proceed"));
			} else {
				var me = this;
				return this.frm.call({
					doc: me.frm.doc,
					method: "set_missing_values",
					callback: function(r) {
						if(!r.exc) {
							me.frm.script_manager.trigger("update_stock");
							frappe.model.set_default_values(me.frm.doc);
							me.set_dynamic_labels();
							me.calculate_taxes_and_totals();
							if(callback_fn) callback_fn();
						}
					}
				});
			}
		}
	},

	customer: function() {
		var me = this;
		if(this.frm.updating_party_details) return;

		erpnext.utils.get_party_details(this.frm,
			"erpnext.accounts.party.get_party_details", {
				posting_date: this.frm.doc.posting_date,
				party: this.frm.doc.customer,
				party_type: "Customer",
				account: this.frm.doc.debit_to,
				price_list: this.frm.doc.selling_price_list,
			}, function() {
			me.apply_pricing_rule();
		})
	},

	debit_to: function() {
		this.customer();
	},

	allocated_amount: function() {
		this.calculate_total_advance("Sales Invoice", "advance_adjustment_details");
		this.frm.refresh_fields();
	},

	write_off_outstanding_amount_automatically: function() {
		if(cint(this.frm.doc.write_off_outstanding_amount_automatically)) {
			frappe.model.round_floats_in(this.frm.doc, ["grand_total", "paid_amount"]);
			// this will make outstanding amount 0
			this.frm.set_value("write_off_amount",
				flt(this.frm.doc.grand_total - this.frm.doc.paid_amount,
					precision("write_off_amount"))
			);
		}

		this.calculate_outstanding_amount(false);
		this.frm.refresh_fields();
	},

	write_off_amount: function() {
		this.write_off_outstanding_amount_automatically();
	},

	paid_amount: function() {
		this.write_off_outstanding_amount_automatically();
	},

	entries_add: function(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		this.frm.script_manager.copy_from_first_row("entries", row, ["income_account", "cost_center"]);
	},

	set_dynamic_labels: function() {
		this._super();
		this.hide_fields(this.frm.doc);
	},

	entries_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_no(grid_row)
	}

});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceController({frm: cur_frm}));

// Hide Fields
// ------------
cur_frm.cscript.hide_fields = function(doc) {
	par_flds = ['project_name', 'due_date', 'is_opening', 'source', 'total_advance', 'gross_profit',
	'gross_profit_percent', 'get_advances_received',
	'advance_adjustment_details', 'sales_partner', 'commission_rate',
	'total_commission', 'advances', 'from_date', 'to_date'];

	item_flds_normal = ['sales_order', 'delivery_note']

	if(cint(doc.is_pos) == 1) {
		hide_field(par_flds);
		unhide_field('payments_section');
		cur_frm.fields_dict['entries'].grid.set_column_disp(item_flds_normal, false);
	} else {
		hide_field('payments_section');
		for (i in par_flds) {
			var docfield = frappe.meta.docfield_map[doc.doctype][par_flds[i]];
			if(!docfield.hidden) unhide_field(par_flds[i]);
		}
		cur_frm.fields_dict['entries'].grid.set_column_disp(item_flds_normal, true);
	}

	item_flds_stock = ['batch_no', 'actual_qty', 'expense_account', 'warehouse']
	cur_frm.fields_dict['entries'].grid.set_column_disp(item_flds_stock,
		(cint(doc.update_stock)==1 ? true : false));

	// India related fields
	if (frappe.boot.sysdefaults.country == 'India') unhide_field(['c_form_applicable', 'c_form_no']);
	else hide_field(['c_form_applicable', 'c_form_no']);

	cur_frm.refresh_fields();
}


cur_frm.cscript.mode_of_payment = function(doc) {
	return cur_frm.call({
		method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_bank_cash_account",
		args: { mode_of_payment: doc.mode_of_payment },
	});
}

cur_frm.cscript.update_stock = function(doc, dt, dn) {
	cur_frm.cscript.hide_fields(doc, dt, dn);
}

cur_frm.cscript.is_opening = function(doc, dt, dn) {
	hide_field('aging_date');
	if (doc.is_opening == 'Yes') unhide_field('aging_date');
}

cur_frm.cscript['Make Delivery Note'] = function() {
	frappe.model.open_mapped_doc({
		method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_delivery_note",
		frm: cur_frm
	})
}

cur_frm.cscript.make_bank_voucher = function() {
	return frappe.call({
		method: "erpnext.accounts.doctype.journal_voucher.journal_voucher.get_payment_entry_from_sales_invoice",
		args: {
			"sales_invoice": cur_frm.doc.name
		},
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
		}
	});
}

cur_frm.fields_dict.debit_to.get_query = function(doc) {
	return{
		filters: {
			'report_type': 'Balance Sheet',
			'group_or_ledger': 'Ledger',
			'company': doc.company
		}
	}
}

cur_frm.fields_dict.cash_bank_account.get_query = function(doc) {
	return{
		filters: {
			'report_type': 'Balance Sheet',
			'group_or_ledger': 'Ledger',
			'company': doc.company
		}
	}
}

cur_frm.fields_dict.write_off_account.get_query = function(doc) {
	return{
		filters:{
			'report_type': 'Profit and Loss',
			'group_or_ledger': 'Ledger',
			'company': doc.company
		}
	}
}

// Write off cost center
//-----------------------
cur_frm.fields_dict.write_off_cost_center.get_query = function(doc) {
	return{
		filters:{
			'group_or_ledger': 'Ledger',
			'company': doc.company
		}
	}
}

//project name
//--------------------------
cur_frm.fields_dict['project_name'].get_query = function(doc, cdt, cdn) {
	return{
		query: "erpnext.controllers.queries.get_project_name",
		filters: {'customer': doc.customer}
	}
}

// Income Account in Details Table
// --------------------------------
cur_frm.set_query("income_account", "entries", function(doc) {
	return{
		query: "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_income_account",
		filters: {'company': doc.company}
	}
});

// expense account
if (sys_defaults.auto_accounting_for_stock) {
	cur_frm.fields_dict['entries'].grid.get_field('expense_account').get_query = function(doc) {
		return {
			filters: {
				'report_type': 'Profit and Loss',
				'company': doc.company,
				'group_or_ledger': 'Ledger'
			}
		}
	}
}


// Cost Center in Details Table
// -----------------------------
cur_frm.fields_dict["entries"].grid.get_field("cost_center").get_query = function(doc) {
	return {
		filters: {
			'company': doc.company,
			'group_or_ledger': 'Ledger'
		}
	}
}

cur_frm.cscript.income_account = function(doc, cdt, cdn) {
	cur_frm.cscript.copy_account_in_all_row(doc, cdt, cdn, "income_account");
}

cur_frm.cscript.expense_account = function(doc, cdt, cdn) {
	cur_frm.cscript.copy_account_in_all_row(doc, cdt, cdn, "expense_account");
}

cur_frm.cscript.cost_center = function(doc, cdt, cdn) {
	cur_frm.cscript.copy_account_in_all_row(doc, cdt, cdn, "cost_center");
}

cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
	if(cint(frappe.boot.notification_settings.sales_invoice)) {
		cur_frm.email_doc(frappe.boot.notification_settings.sales_invoice_message);
	}

	$.each(doc["entries"], function(i, row) {
		if(row.delivery_note) frappe.model.clear_doc("Delivery Note", row.delivery_note)
	})
}

cur_frm.cscript.send_sms = function() {
	frappe.require("assets/erpnext/js/sms_manager.js");
	var sms_man = new SMSManager(cur_frm.doc);
}

//Rohit
cur_frm.cscript.validate = function(doc, cdt, cdn){	
setTimeout(function(){
refresh_field(['entries','net_total_export','grand_total_export','outstanding_amount','rounded_total_export','in_words_export','work_order_distribution']);
},1000)

}
//for tailoring products
cur_frm.cscript.tailoring_item_code = function(doc, cdt, cdn){
var d = locals[cdt][cdn]
get_server_fields('get_details',d.tailoring_item_code,'',doc, cdt, cdn, 1 , function(doc, cdt, cdn){
refresh_field('sales_invoice_items_one')
})
}
cur_frm.cscript.tailoring_qty = function(doc, cdt, cdn){
cur_frm.cscript.calculate_tailoring_amount(doc, cdt, cdn);
}	
cur_frm.cscript.tailoring_rate = function(doc, cdt, cdn){
cur_frm.cscript.calculate_tailoring_amount(doc, cdt, cdn);
}
cur_frm.cscript.tailoring_discount_percentage = function(doc, cdt, cdn){
cur_frm.cscript.calculate_tailoring_amount(doc, cdt, cdn);	
}
cur_frm.cscript.calculate_tailoring_amount = function(doc, cdt, cdn){
var d = locals[cdt][cdn]
if(d.tailoring_discount_percentage == 100.0)
{
d.tailoring_amount = 0	
}
else
{
if(d.tailoring_discount_percentage)
{
d.tailoring_amount = flt(d.tailoring_rate * (1.0 - (flt(d.tailoring_discount_percentage) / 100.0))*d.tailoring_qty)
}
else{
d.tailoring_amount = flt(flt(d.tailoring_rate) *flt(d.tailoring_qty))
}
}
refresh_field('sales_invoice_items_one')
cur_frm.cscript.calculate_net_total(doc, cdt, cdn)
}
//for merchandise products
cur_frm.cscript.merchandise_item_code = function(doc, cdt, cdn){
var d = locals[cdt][cdn]
get_server_fields('get_merchandise_details',d.merchandise_item_code,'',doc, cdt, cdn, 1 , function(doc, cdt, cdn){
refresh_field('merchandise_item')
})
}
cur_frm.cscript.merchandise_qty = function(doc, cdt, cdn){
cur_frm.cscript.calculate_merchandise_amount(doc, cdt, cdn);
}
cur_frm.cscript.merchandise_rate = function(doc, cdt, cdn){
cur_frm.cscript.calculate_merchandise_amount(doc, cdt, cdn);
}
cur_frm.cscript.merchandise_discount_percentage = function(doc, cdt, cdn){
cur_frm.cscript.calculate_merchandise_amount(doc, cdt, cdn);
}
cur_frm.cscript.calculate_merchandise_amount = function(doc, cdt, cdn){
var d = locals[cdt][cdn]
if(d.merchandise_discount_percentage == 100.0)
{
d.merchandise_amount = 0
}
else
{
if(d.merchandise_discount_percentage)
{
d.merchandise_amount = flt(d.merchandise_rate * (1.0 - (d.merchandise_discount_percentage / 100.0))*d.merchandise_qty)
}
else{
d.merchandise_amount = flt(flt(d.merchandise_rate) *flt(d.merchandise_qty))
}
}
refresh_field('merchandise_item')
cur_frm.cscript.calculate_net_total(doc, cdt, cdn)
}
cur_frm.cscript.sales_invoice_items_one_remove = function(doc, cdt, cdn){
cur_frm.cscript.calculate_net_total(doc, cdt, cdn)
}
cur_frm.cscript.merchandise_item_remove = function(doc, cdt, cdn){
cur_frm.cscript.calculate_net_total(doc, cdt, cdn)
}
cur_frm.cscript.calculate_net_total = function(doc, cdt, cdn){
if (doc){
var net_total = 0.0
var cl=doc.sales_invoice_items_one || [ ]
for(i=0 ;i<cl.length;i++){
net_total += parseFloat(cl[i].tailoring_amount)
}
var al = doc.merchandise_item || [ ]
for(i=0 ;i<al.length;i++){
net_total += parseFloat(al[i].merchandise_amount)
}
doc.net_total_export = net_total
refresh_field('net_total_export')
}
}

cur_frm.fields_dict['sales_invoice_items_one'].grid.get_field('tailoring_item_code').get_query = function(doc) {
	return{
		filters: {
			'item_group': 'Tailoring'
		}
	}
}

cur_frm.fields_dict['merchandise_item'].grid.get_field('merchandise_item_code').get_query = function(doc) {
	return{
		filters: {
			'item_group': 'Merchandise'
		}
	}
}

cur_frm.fields_dict['sales_invoice_items_one'].grid.get_field('fabric_code').get_query = function(doc) {
	return{
		filters: [
			['Item', 'item_group', 'in', 'Fabric, Fabric Swatch Item']
		]
	}
}

cur_frm.cscript.tailoring_size = function(doc, cdt, cdn){
	cur_frm.cscript.set_qty(doc, cdt, cdn)
}

cur_frm.cscript.width = function(doc, cdt, cdn){
	cur_frm.cscript.set_qty(doc, cdt, cdn)	
}

cur_frm.cscript.set_qty = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	get_server_fields('get_size_details',d.idx,'',doc,cdt,cdn,1,function(){
		refresh_field('sales_invoice_items_one')
	})
}

cur_frm.fields_dict['work_order_distribution'].grid.get_field('tailor_work_order').get_query = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	return{
		filters: {
			'sales_invoice_no': null || doc.name,
			'item_code': d.tailoring_item_code
		}
	}
}



{% include 'stock/custom_items.js' %}
$.extend(cur_frm.cscript, new erpnext.stock.SplitQty({frm: cur_frm}));



// cur_frm.script_manager.make(erpnext.account.CustomJs);
var fabric_detail = {}

cur_frm.cscript.reserve_fabric = function(doc, cdt, cdn){
	var e =locals[cdt][cdn]
	var image_data;
	var dialog = new frappe.ui.Dialog({
			title:__(e.field_name+' Styles'),
			fields: [
				{fieldtype:'HTML', fieldname:'styles_name', label:__('Styles'), reqd:false,
					description: __("")},
					{fieldtype:'Button', fieldname:'create_new', label:__('Ok') }
			]
		})
	var fd = dialog.fields_dict;

        // $(fd.styles_name.wrapper).append('<div id="style">Welcome</div>')
        return frappe.call({
			type: "GET",
			method: "tools.tools_management.custom_methods.get_warehouse_wise_stock_balance",
			args: {
				"item": e.fabric_code,
				"qty": e.fabric_qty
			},
			callback: function(r) {
				if(r.message) {
					
					var result_set = r.message;
					this.table = $("<table class='table table-bordered'>\
                       <thead><tr></tr></thead>\
                       <tbody></tbody>\
                       </table>").appendTo($(fd.styles_name.wrapper))

					columns =[['','10'],['Warehouse','40'],['Qty','40']]
					var me = this;
					$.each(columns, 
                       function(i, col) {                  
                       $("<th>").html(col[0]).css("width", col[1]+"%")
                               .appendTo(me.table.find("thead tr"));
                  }	);
					
					$.each(result_set, function(i, d) {
						var row = $("<tr>").appendTo(me.table.find("tbody"));
                       $("<td>").html('<input type="radio" name="sp" value="'+d[0]+'">')
                       		   .attr("style", d[0])
                               .attr("image", d[1])
                               .appendTo(row)
                               .click(function() {
                                      if(fabric_detail[d[1]]){
                                      	fabric_detail[d[1]].push([e.fabric_code, e.fabric_qty, e.tailoring_item_code])
                                      }
                                      else{
                                      	fabric_detail[d[1]] = []
                                       	fabric_detail[d[1]].push([e.fabric_code, e.fabric_qty, e.tailoring_item_code])
                                       }
                               });
                     
                       $("<td>").html(d[1]).appendTo(row);
                       $("<td>").html(d[0]).appendTo(row);                    
               });
					
					dialog.show();
					$(fd.create_new.input).click(function() {
						doc.fabric_details = JSON.stringify(fabric_detail)					
						refresh_field('fabric_details')
						e.reservation_status = 'Reserved';
						refresh_field('reservation_status', e.name, 'sales_invoice_items_one')	
						dialog.hide()
					})
				}
			}
		})	
}