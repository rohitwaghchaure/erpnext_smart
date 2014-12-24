cur_frm.cscript.onload = function(doc, cdt, cdn){
	console.log(doc.__islocal)
	if(doc.__islocal){
		doc.date = frappe.datetime.get_today()
		refresh_field('date')

		if(doc.branch){
			load_ad_details(doc, cdt, cdn)
		}
	}
}

cur_frm.cscript.branch= function(doc, cdt, cdn){
	load_ad_details(doc, cdt, cdn)
}

load_ad_details = function(doc, cdt, cdn){
	return $c('runserverobj',args={'method':'get_employee', 'docs':doc}, function(r,rt) {
			refresh_field('ad_details')
		})
}

cur_frm.cscript.presenty_status= function(doc, cdt, cdn){
	var ad = doc.ad_details || [ ]
	for(i=0;i<ad.length;i++){
		ad[i].status = doc.presenty_status;
	}
	refresh_field('ad_details')
}