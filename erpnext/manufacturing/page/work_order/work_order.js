frappe.pages['work-order'].onload = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Work Order',
		single_column: true
	});

	$("<div class='user-settings'></div>\
	<table width = '100%'>\
		<tr>\
			<td width = '100%' valign='top'><div id= 'result_area'></div></td>\
		</tr>\
	</table>").appendTo($(wrapper).find(".layout-main").empty());
	work_order = ''
	if(frappe.route_options){
		work_order = frappe.route_options.work_order
	}

	wrapper.permission_engine = new frappe.WOForm(wrapper, work_order, frappe.route_options.args);
}

frappe.pages['work-order'].refresh = function(wrapper) {
	wrapper.permission_engine.set_from_route();
}


frappe.WOForm = Class.extend({
	init: function(wrapper, woname, args){
		this.wrapper = wrapper;
		this.args = args
		this.woname = woname;
		this.style_details = {}
		this.field_list = {
			"Work Order":[
					['Sales Invoice No','Link','Sales Invoice','sales_invoice_no'],
					['Item code', 'Link', 'Item', 'item_code'],
					['Customer Name', 'Data', '', 'customer'],
					['Serial NO', 'Small Text', '', 'serial_no_data']
				],
			"Style Transactions":[
					['Field Name', 'Link', 'Style', 'field_name']
				],
			"Measurement Item":[
					['Parameter', 'Link', 'Measurement', 'parameter'],
					['Abbreviation', 'Data', '', 'abbreviation'],
					['Value', 'Float', '', 'value']
				]
		}

		this.render_wo_form();
		
	},

	set_from_route: function() {
		var me = this;
		console.log([frappe.get_route()[1]])
		if(frappe.get_route()[1]) {
			woname = frappe.get_route()[1];
			args = '';
		} else if(frappe.route_options) {
			console.log(frappe.route_options.args)
			if(frappe.route_options.work_order) {
				woname = frappe.route_options.work_order;
				args = frappe.route_options.args;
			}
		}
		new frappe.WOForm(me.wrapper, woname, args);
	},

	render_wo_form: function(){
		var me = this;
		$('#result_area').empty()
		this.field_area = $(this.wrapper).find('#result_area')

		$.each(this.field_list, 
			function(i, field) {
				me.table1 = $("<table>\
						<tbody style='display: block;width:500px;'></tbody>\
						</table>").appendTo(me.field_area);
				me.render_child(field, i)

		})

		$("<button class='btn btn-small btn-primary' style='margin-bottom:2%; margin-left:30%'><i class='icon-save'></i> Save </button>")
		.appendTo(me.field_area)
		.click(function() {
			me.update_wo()
			// window.open("#Form/Customer/"+$('[data-fieldname="customer_name"]').val(), "_self");
		});

		$("<button class='btn btn-small btn-primary' style='margin-bottom:2%;margin-left:5%'><i class='icon-folder-open'></i> Open </button>")
		.appendTo(me.field_area)
		.click(function() {
			// me.update_wo()
			window.open("#Form/Work Order/"+me.woname, "_self");
		});
	
	

		$('#result_area').css('margin-left','2%').css('padding-right','2%').css('border','2px solid').css('border-color','#F2F0F0').css("padding-top","2%")
	},
	render_child: function(fields, key){
		var me = this;

		$('<h4 class="col-md-12" style="margin: 0px 0px 15px;">\
			<i class="icon-in-circle icon-user"></i>\
			<span class="section-count-label"></span>.'+key+'. </h4>').prependTo(me.table1)

		var row = $("<tr>").appendTo(me.table1.find("tbody"));
		$.each(fields, 
			function(i, field) {
				$('<td>').html('<label class="control-label" style="align:center;margin-top:2%;margin-left:10%">'+field[0]+'</label>').appendTo(row);
				
				if(i%2 == 1){
					row = $("<tr>").appendTo(me.table1.find("tbody"));
					for(j=i-1; j<=(i); j++){
						var td = $("<td>").appendTo(row)
						frappe.ui.form.make_control({
							df: {
							    "fieldtype": fields[j][1],
								"fieldname": fields[j][3],
								"options": fields[j][2],
								"label": fields[j][0]
								},
							parent:td,
						}).make_input();

					}
					row = $("<tr>").appendTo(me.table1.find("tbody"));
				}
				else if(i == fields.length-1){
					row = $("<tr>").appendTo(me.table1.find("tbody"));
					var td = $("<td>").appendTo(row)
					frappe.ui.form.make_control({
							df: {
							    "fieldtype": fields[i][1],
								"fieldname": fields[i][3],
								"options": fields[i][2],
								"label": fields[i][0]
								},
							parent:td,
						}).make_input();
				}
			})

		$( "label" ).remove( ".col-xs-4" );
		$( "div.col-xs-8" ).addClass( "col-xs-12" )
		$( "div" ).removeClass( "col-xs-8" );
		$( "div.col-xs-12" ).css('padding','2%');

		if(key!='Work Order'){

			$("<button class='btn btn-small btn-primary' style='margin-bottom:2%' id='"+key+"'><i class='icon-plus'></i></button>")
			.appendTo($("<td colspan='2' align='center'>").appendTo(row))
			.click(function() {
				me.add_row($(this).attr('id'))
			});

			if(key == 'Style Transactions')
				columns = [["Field Name",50], ["Name", 100], ["Abbreviation", 100], ['Image', 100],["View", 100]];
			if(key == 'Measurement Item')
				columns = [["Parameter",50], ["Abbreviation", 100], ["Value", 100]];

			id_val = 'measurement_details'
			if (key=='Style Transactions'){
				id_val = 'style_details'
			}
			this[key] =$("<table class='table table-bordered' id='"+id_val+"'>\
				<thead><tr></tr></thead>\
				<tbody></tbody>\
			</table>").appendTo(me.field_area)

			$.each(columns, 
				function(i, col) {
				$("<th>").html(col[0]).css("width", col[1]+"px")
					.appendTo(me[key].find("thead tr"));
			});
		}

		this.render_data(key);
	},
	render_data: function(key){
		var me = this;
		frappe.call({
			method:"mreq.mreq.page.sales_dashboard.sales_dashboard.get_wo_details",
			args:{'tab': key, 'woname': this.woname},
			callback: function(r){
				$.each(r.message, function(i, d) {	
					me.create_child_row(key, d)
				});
			}
		})
	},
	add_row:function(key){
		var me = this;
		me.create_child_row(key)
	},
	create_child_row: function(key, dic){
		var me = this;

		if(key == 'Work Order') {
			$.each(dic, function(key, val){
				$('[data-fieldname="'+key+'"]').attr("disabled","disabled")
				$('[data-fieldname="'+key+'"]').val(val)
			})
		};

		var row = $("<tr>").appendTo(me[key].find("tbody")[0]);

		if(key == 'Style Transactions'){
			if(!dic){
				dic = {'field_name': $('[data-fieldname="field_name"]').val(), 'abbreviation': ''} 
			}
			$("<td>").html(dic['field_name']).appendTo(row);
			$("<td>").html('<input type="Textbox" class="text_box">').appendTo(row);
			$("<td>").html(dic['abbreviation']).appendTo(row);
			$("<td>").appendTo(row);
			$('<button  class="remove">View</button>').appendTo($("<td>")).appendTo(row)
				.click(function(){
					me.view_style($(this).closest("tr").find('td'), me[key].find("tbody"))
				});
		}
		else if(key == 'Measurement Item'){
			if(!dic){
				dic = {
					'parameter': $('[data-fieldname="parameter"]').val(), 
					'abbreviation': $('[data-fieldname="abbreviation"]').val(),
					'value': $('[data-fieldname="value"]').val()
				} 
			}
			$("<td>").html(dic['parameter']).appendTo(row);
			$("<td>").html(dic['abbreviation']).appendTo(row);
			$('<input type="text" class="text_box">').appendTo($("<td>")).appendTo(row)
				.focusout(function(){
					me.calc_measurement($(this).closest("tbody").find('tr'), $(this).closest("tr").find('td'), $(this).val())
				})
				.val(dic['value'])
		}
	},
	view_style:function(col_id, tab){
		var style_name = $(col_id[0]).text();
		var image_data;
		alert($(this).parent().index())
		var me1 = this;
		var dialog = new frappe.ui.Dialog({
				title:__(style_name+' Styles'),
				fields: [
					{fieldtype:'HTML', fieldname:'styles_name', label:__('Styles'), reqd:false,
						description: __("")},
						{fieldtype:'Button', fieldname:'create_new', label:__('Ok') }
				]
			})
		var fd = dialog.fields_dict;
	        return frappe.call({
				type: "GET",
				method: "tools.tools_management.custom_methods.get_styles_details",
				args: {
					"item": $('[data-fieldname="item_code"]').val(),
					"style": style_name 
				},
				callback: function(r) {
					if(r.message) {
						
						var result_set = r.message;
						this.table = $("<table class='table table-bordered'>\
	                       <thead><tr></tr></thead>\
	                       <tbody></tbody>\
	                       </table>").appendTo($(fd.styles_name.wrapper))

						columns =[['Style','10'],['Image','40'],['Value','40']]
						var me = this;
						$.each(columns, 
	                       function(i, col) {                  
	                       $("<th>").html(col[0]).css("width", col[1]+"%")
	                               .appendTo(me.table.find("thead tr"));
	                  }	);
						
						$.each(result_set, function(i, d) {
							var row = $("<tr>").appendTo(me.table.find("tbody"));
	                       $("<td>").html('<input type="radio" name="sp" value="'+d[0]+'">')
	                       		   .attr("style", d[0])
	                               .attr("image", d[1])
	                               .attr("value", d[2])
	                               .attr("abbr", d[3])
	                               .attr("customer_cost", d[4])
	                               .attr("tailor_cost", d[5])
	                               .attr("extra_cost", d[6])
	                               .appendTo(row)
	                               .click(function() {
	                               		  $(col_id[3]).html('<img width="80px" height="50px" src='+$($(this).attr('image')).find('img').attr('src')+'>')
	                               });
	                     
	                       $("<td>").html($(d[1]).find('img')).appendTo(row);
	                       $("<td>").html(d[2]).appendTo(row);                    
	               });
						dialog.show();
						$(fd.create_new.input).click(function() {						
							refresh_field('wo_style')	
							dialog.hide()
						})
					}
				}
			})	
	},
	calc_measurement: function(tr, td, value){
		var measurement_details = []
		var param_args = {'parameter':$(td[0]).text(), 'value':value, 
			'item':$('[data-fieldname="item_code"]').val()}

		$.each(tr, function(d,i){
			measurement_details.push({'value':$(i).find('.text_box').val(),'parameter': $($(i).find('td')[0]).text()})
		})
		
		frappe.call({
			method:"erpnext.manufacturing.doctype.work_order.work_order.apply_measurement_rules",
			args:{'measurement_details': measurement_details, 'param_args':param_args},
			callback:function(r){
				$.each(tr, function(d,i){
					for(key in r.message){
						if($($(i).find('td')[0]).text() == r.message[key]['parameter'])
							$(i).find('.text_box').val(r.message[key]['value'])
					}
				})
			}
		})
	},
	update_wo: function(){
		var me = this;
		this.wo_details = {}
		$.each(me.field_area.find('#style_details tbody tr'), function(i){
			style_dict = {}
			var key = ['field_name', 'default_value', 'abbreviation', 'image_viewer']
			cells = $(this).find('td')
			$.each(cells, function(i){
				style_dict[key[i]] = $(this).text() || $(this).find('.text_box').val() || $(this).find('img').attr('src') || ''	
			})
			console.log(style_dict)
			me.style_details[i] = style_dict
		})

		$.each(me.field_area.find('#measurement_details tbody tr'), function(i){
			measurement_dict = {}
			var key = ['parameter', 'abbreviation']
			cells = $(this).find('td')
			$.each(cells, function(i){
				measurement_dict[key[i]] = $(this).text() || ''	
			})
			measurement_dict['value'] = $(this).find('.text_box').val()
			me.wo_details[i] = measurement_dict
		})
		
		
		frappe.call({
			method:"mreq.mreq.page.sales_dashboard.sales_dashboard.create_work_order",
			args:{'wo_details': me.wo_details, 'style_details':me.style_details, 'fields':me.field_list, 'woname': me.woname,'args': me.args, 'type_of_wo':'amend'},
			callback: function(r){
				// new frappe.SalesInvoce(me.wrapper)
			}
		})
	}
})


