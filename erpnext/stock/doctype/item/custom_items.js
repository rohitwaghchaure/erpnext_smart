

frappe.provide("erpnext.stock");
frappe.require("assets/erpnext/js/controllers/stock_controller.js");

erpnext.stock.CustomItem = erpnext.stock.StockController.extend({ 
 
   items_image: function(doc) {
      var image_data;
      var dialog = new frappe.ui.Dialog({
        title:__('Images'),
        fields: [{fieldtype:'HTML', fieldname:'image_name', label:__('Images'), reqd:false,
                  description: __("")}
                ]})

        var fd = dialog.fields_dict;
        return frappe.call({
            type: "GET",
            method: "erpnext.stock.stock_custom_methods.get_details",
            args: {
              "item_name": doc.item_name
            },
            callback: function(r) {
              var me = this;
              if(r.message)
              {
              result_set=r.message
              this.table = $('<div id="banner-slide" style="height:200px; width:300px;  textAlign:center">\
              <ul class="bjqs">\
              </ul></div>').appendTo($(fd.image_name.wrapper));
              $.each(result_set,function(i,d) {  
              var row = $("<li>").appendTo(me.table.find("ul"));
                        $("<li>").html('<li><img src="'+d[0]+'" width="500px" text-align="center" title="secound caption"></li>')
                               .appendTo(me.table.find(row));
                  });
                  this.table.bjqs({
                  height      : 500,
                  width       : 500,
                  responsive  : true,
                  randomstart   : true
                  });
                  dialog.show();
                }
                else
                {
                  msgprint("No Images Found");
                }
              }
          });
    }

  })

