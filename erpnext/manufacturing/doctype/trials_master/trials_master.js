cur_frm.fields_dict.trials_transaction.grid.get_field("trial_good_serial_no").get_query = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	return {
		filters: {
			"item_code": d.trial_product
		}
	}
}

cur_frm.fields_dict.trials_transaction.grid.get_field("trial_product").get_query = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	return {
		filters: {
			"item_category": "Dummy"
		}
	}
}

cur_frm.cscript.validate = function(doc, cdt, cdn){
	setTimeout(function(){
refresh_field('trials_transaction')
},1000)
	
}