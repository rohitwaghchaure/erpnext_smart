cur_frm.cscript.view_image = function(doc, cdt, cdn){
	var d = locals[cdt][cdn]
	d.user_image_show = '<table style="width: 100%; table-layout: fixed;"><tr><td><img src="'+d.view_image+'" width="100px"></td></tr></table>'
	refresh_field("product_catlog_image");
}


cur_frm.fields_dict['product'].get_query = function(doc) {
	return {
		filters: {
			"item_group": "Fabric", 
		}
	}
}