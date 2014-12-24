cur_frm.cscript.refresh =  function(doc, cdt, cdn){
	get_server_fields('get_image_view','','', doc, cdt, cdn, 1 , function(){
		refresh_field('image_view')
	})
}

cur_frm.cscript.upload_image = function(doc, cdt, cdn){
	get_server_fields('get_update_image_view',doc.upload_image,'', doc, cdt, cdn, 1 , function(){
		refresh_field('image_view')
	})
}