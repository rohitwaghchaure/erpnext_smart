cur_frm.cscript.work_order_changes = function(doc, cdt, cdn){

	var d =locals[cdt][cdn]
	if(d.work_order){
		frappe.route_options = { work_order: d.work_order, args: d};
		frappe.set_route("work-order");		
	}else{
		alert("Work order is not defined")
	}
	
}


cur_frm.fields_dict['trial_serial_no'].get_query = function(doc, cdt, cdn) {
      	return {
      		query : "tools.tools_management.custom_methods.get_serial_no",
      		filters : {
      			'serial_no':doc.serial_no_data
      		}
      	}
}

cur_frm.cscript.trial_serial_no = function(doc, cdt, cdn) {
    get_server_fields('update_status', '','',doc, cdt, cdn, 1, function(){
		// hide_field('trial_serial_no');
		refresh_field('trials_serial_no_status')
	})  	
}

cur_frm.cscript.validate= function(doc){
	if(doc.trials_serial_no_status){
		hide_field('trial_serial_no');
	}
	setTimeout(function(){refresh_field(['trial_dates', 'completed_process_log'])}, 1000)
}

cur_frm.cscript.refresh= function(doc){
	if(doc.trials_serial_no_status){
		hide_field('trial_serial_no');
	}
}

cur_frm.cscript.finished_all_trials = function(doc){
	var cl = doc.trial_dates || [ ]
	$.each(cl, function(i){
		if(cl[i].production_status!='Closed'){
			cl[i].skip_trial = parseInt(doc.finished_all_trials)
		}
	})
	refresh_field('trial_dates')
}

cur_frm.cscript.work_status = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	var cl = doc.trial_dates || [ ]

	if(d.work_status == 'Open'){

		$.each(cl, function(i){
			if(cl[i].production_status!='Closed' && parseInt(cl[i].idx) < parseInt(d.idx)){
				cl[i].next_trial_no = d.trial_no
			}
		})
	}
	refresh_field('trial_dates')
}

cur_frm.fields_dict['finish_trial_for_process'].get_query = function(doc, cdt, cdn) {
		get_finished_list = cur_frm.cscript.get_finished_list(doc)
      	return {
      		query : "tools.tools_management.custom_methods.get_unfinished_process",
      		filters : {
      			'item_code':doc.item_code,
      			'get_finished_list' : get_finished_list
      		}
      	}
}

cur_frm.cscript.get_finished_list= function(doc){
	var cl = doc.completed_process_log || [ ]
	var process_list = ""
	if (parseInt(cl.length) > 1){
		$.each(cl, function(i){
			if(cl[i].completed_process && process_list){
				process_list = process_list + ",'" + cl[i].completed_process + "'"
			}else{
				process_list = "'" + cl[i].completed_process + "'"
			}
		})
		process_list = "(" + process_list + ")"
	}
	return process_list
}

cur_frm.cscript.trial_dates_add = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	if(doc.trial_serial_no){
		d.subject = doc.trial_serial_no
		refresh_field('trial_dates')
	}else{
		alert("Select serial no")
	}
}