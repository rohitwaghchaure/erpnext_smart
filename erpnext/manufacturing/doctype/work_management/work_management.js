cur_frm.cscript.onload= function(doc ,cdt,cdn){
	get_server_fields('get_invoice_details', '','',doc,cdt,cdn , 1 , function(){
		refresh_field('production_details')
	})
}

cur_frm.cscript.sales_invoice_no = function(doc, cdt, cdn){
	get_server_fields('get_invoice_details', doc.sales_invoice_no,'',doc,cdt,cdn , 1 , function(){
		refresh_field('production_details')
	})	
}

cur_frm.cscript.services = function(doc, cdt, cdn){
	get_server_fields('get_invoice_details', doc.sales_invoice_no,'',doc,cdt,cdn , 1 , function(){
		refresh_field('production_details')
	})	
}

cur_frm.cscript.search = function(doc, cdt, cdn){
	var s =document.getElementById('view');
	s.src = 'http://localhost:9777/desk#Form/Sales Invoice/SINV-00039';
	cur_frm.cscript.sales_invoice_no(doc, cdt, cdn)
}

cur_frm.cscript.select = function(doc, cdt, cdn){
	var d =locals[cdt][cdn]
	get_server_fields('save_data',d,'',doc, cdt,cdn,1,function(){
		refresh_field('production_details')
	})
}

cur_frm.cscript.refresh = function(doc, cdt, cdn){

	get_server_fields('clear_data','','',doc, cdt,cdn,1,function(){
		refresh_field('production_details')
	})
}

cur_frm.fields_dict['sales_invoice_no'].get_query = function(doc) {
	return {
		filters: {
			"docstatus": 1,
		}
	}
}

cur_frm.fields_dict.production_details.grid.get_field("process_allotment").get_query = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	return {
		filters: {
			"sales_invoice_no": d.sales_invoice,
			"docstatus": 0 || 1,
			"item": d.article_code
		}
	}
}

cur_frm.fields_dict.production_details.grid.get_field("work_order").get_query = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	return {
		filters: {
			"sales_invoice_no": d.sales_invoice,
			"docstatus": 0 || 1,
			"item_code": d.article_code
		}
	}
}

cur_frm.cscript.process_allocation = function(doc, cdt, cdn){
	d = locals[cdt][cdn]
	this.div;
	return frappe.call({
		type :'Get',
		method : 'erpnext.accounts.accounts_custom_methods.get_process_detail',
		args:{
			'name':d.process_allotment
		},
		callback : function(r){
			var dialog = new frappe.ui.Dialog({
			title:__('Process'),
			fields: [
				{fieldtype:'HTML', fieldname:'styles_name', label:__('Styles'), reqd:false,
					description: __("")},
					{fieldtype:'Button', fieldname:'ok', label:__('Ok') }
			]
		})
		var fd = dialog.fields_dict;
		$(this.div).find('myDiv').remove()
		this.div = $('<div id="myDiv"><table class="table table-bordered" style="background-color: #D8D8D8;height:10px" id="mytable"><thead><tr><td>Process Name</td><td>Process</td><td>Trials</td><td>QC Status</td></tr></thead><tbody></tbody></table></div>').appendTo($(fd.styles_name.wrapper))
		for(i=0;i<r.message.length;i++){
			
				this.table = $(this.div).find('#mytable').append('<tr style="background-color: #FFFFFF;"><td><a href="#Form/Process Allotment/'+r.message[i].process_data+'">'+r.message[i].process_data+'</a></td><td>'+r.message[i].process_name+'</td><td>'+r.message[i].trials+'</td><td>'+r.message[i].qi_status+'</td></tr>')
			
		}
		dialog.show()

		$(fd.ok.input).click(function(){
			dialog.hide()
		})
		}

	})
}
