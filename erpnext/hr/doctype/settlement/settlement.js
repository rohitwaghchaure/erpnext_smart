cur_frm.cscript.onload= function(doc,cdt,cdn){
	if(doc.__islocal){
		doc.date = frappe.datetime.get_today()
		refresh_field('date')
	}
}

cur_frm.cscript.employee_id = function(doc, cdt ,cdn){
	return $c('runserverobj',args={'method':'get_details', 'docs':doc}, function(r,rt) {
			refresh_field(['pending_task','loan_detail'])
		})
}