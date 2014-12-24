cur_frm.cscript.add = function(doc, cdt, cdn){
	get_server_fields('get_invoice_details', doc.sales_invoice_no,'',doc,cdt,cdn , 1 , function(){
		refresh_field('cut_order_item')
	})	
}