cur_frm.cscript.refresh = function(doc, cdt, cdn){
	get_server_fields('get_invoices_list','','', doc, cdt, cdn, 1 , function(){
		refresh_field('admin_note')
	})
}

cur_frm.cscript.select_all = function(doc, cdt, cdn){
	var status = doc.admin_note || [ ]
	for(i=0;i<status.length;i++){
		status[i].select = parseInt(doc.select_all)
	}
	refresh_field('admin_note')
}

cur_frm.cscript.apply_status = function(doc, cdt, cdn){
	var status = doc.admin_note || [ ]
	for(i=0;i<status.length;i++){
		status[i].status = doc.apply_status
	}
	refresh_field('admin_note')
}

cur_frm.cscript.process = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	if(parseInt(d.select) == 1){
		get_server_fields('processed_methods',d.sales_invoice,'', doc, cdt, cdn, 1 , function(){
			alert("Done")
			refresh_field('admin_note')
		})	
	}else{
		alert("Click on select check box")
	}
	
}

cur_frm.cscript.processed = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	get_server_fields('processed_methods','','', doc, cdt, cdn, 1 , function(){
		alert("Done")
		refresh_field('admin_note')
	})
}