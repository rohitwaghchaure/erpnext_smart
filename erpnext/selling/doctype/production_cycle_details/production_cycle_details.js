cur_frm.fields_dict.process_details.grid.get_field("source_branch").get_query = function(doc, cdt, cdn) {
		var d = locals[cdt][cdn]
      	return {
      		query : "tools.tools_management.custom_methods.get_branch_of_process",
      		filters : {
      			'item_code':doc.item_code,
      			'process' : d.process
      		}
      	}
}

cur_frm.fields_dict.process_details.grid.get_field("target_branch").get_query = function(doc, cdt, cdn) {
		var d = locals[cdt][cdn]
		var process;
		if(parseInt(d.has_trials)!=1)
		{
			var cl = doc.process_details
			$.each(cl, function(i){
				if(parseInt(d.idx + 1) == parseInt(cl[i].idx)){
					process = cl[i].process
					return;
				}
			})	
		}
		
      	return {
      		query : "tools.tools_management.custom_methods.get_branch_of_process",
      		filters : {
      			'item_code':doc.item_code,
      			'process' : process,
      			'target_branch': d.target_branch
      		}
      	}
}