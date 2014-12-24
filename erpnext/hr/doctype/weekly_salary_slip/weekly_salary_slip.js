
cur_frm.add_fetch('employee', 'company', 'company');

cur_frm.cscript.from_date= function(doc, cdt, cdn) {
	console.log(doc.from_date);
	console.log(doc.to_date);
	if (doc.from_date && doc.to_date)
	{
		if(doc.salary_type == 'Weekly' && frappe.datetime.get_diff(doc.to_date, doc.from_date) <= 8){
			var arg = {'month_start_date':doc.from_date, 'month_end_date':doc.to_date}
			get_server_fields('get_week_details',JSON.stringify(arg),doc.to_date,doc, cdt, cdn, 1 , function(r){

			refresh_field('total_days_in_month')	
			// console.log(r);
			});
		}
		else{
			msgprint("Dates not is same week")
		}
     
	}
};

cur_frm.cscript.to_date= function(doc, cdt, cdn) {
	// console.log(d.from_date);
	// console.log(d.to_date);
	if (doc.from_date && doc.to_date)
	{
		if(doc.salary_type == 'Weekly' && frappe.datetime.get_diff(doc.to_date, doc.from_date) <= 8){
			var arg = {'month_start_date':doc.from_date, 'month_end_date':doc.to_date}
			get_server_fields('get_week_details',JSON.stringify(arg),doc.to_date,doc, cdt, cdn, 1 , function(r){
				console.log(r.total_days_in_month)	
				refresh_field('total_days_in_month');
			});
		}
		else{
			msgprint("Dates not is same week")
		}
	}
};


cur_frm.cscript.onload = function(doc,dt,dn){
	if((cint(doc.__islocal) == 1) && !doc.amended_from){
		if(!doc.from_date&&!doc.to_date) {
			var today=new Date();
			// doc.from_date=today
			// doc.to_date=today
		// 	month = (today.getMonth()+01).toString();
		// 	if(month.length>1) doc.month = month;
		// 	else doc.month = '0'+month;
		}
		if(!doc.fiscal_year) doc.fiscal_year = sys_defaults['fiscal_year'];
		refresh_many(['month', 'fiscal_year']);
	}
}

// Get leave details
//---------------------------------------------------------------------
cur_frm.cscript.fiscal_year = function(doc,dt,dn){
		return $c_obj(doc, 'get_emp_and_leave_details','',function(r, rt) {
			var doc = locals[dt][dn];
			cur_frm.refresh();
			calculate_all(doc, dt, dn);
			refresh_field(['earning_details','deduction_details'])
		});
}



cur_frm.cscript.month = cur_frm.cscript.employee = cur_frm.cscript.fiscal_year;

cur_frm.cscript.leave_without_pay = function(doc,dt,dn){
	if (doc.employee && doc.fiscal_year && doc.month) {
		return $c_obj(doc, 'get_leave_details',doc.leave_without_pay,function(r, rt) {
			var doc = locals[dt][dn];
			cur_frm.refresh();
			calculate_all(doc, dt, dn);
		});
	}
}

var calculate_all = function(doc, dt, dn) {
	calculate_earning_total(doc, dt, dn);
	calculate_ded_total(doc, dt, dn);
	calculate_net_pay(doc, dt, dn);
}

cur_frm.cscript.e_modified_amount = function(doc,dt,dn){
	calculate_earning_total(doc, dt, dn);
	calculate_net_pay(doc, dt, dn);
}

cur_frm.cscript.e_depends_on_lwp = cur_frm.cscript.e_modified_amount;

// Trigger on earning modified amount and depends on lwp
// ------------------------------------------------------------------------
cur_frm.cscript.d_modified_amount = function(doc,dt,dn){
	calculate_ded_total(doc, dt, dn);
	calculate_net_pay(doc, dt, dn);
}

cur_frm.cscript.d_depends_on_lwp = cur_frm.cscript.d_modified_amount;

// Calculate earning total
// ------------------------------------------------------------------------
var calculate_earning_total = function(doc, dt, dn) {
	var tbl = doc.earning_details || [];

	var total_earn = 0;
	for(var i = 0; i < tbl.length; i++){
		if(cint(tbl[i].e_depends_on_lwp) == 1) {
			tbl[i].e_modified_amount = Math.round(tbl[i].e_amount)*(flt(doc.payment_days)/cint(doc.total_days_in_month)*100)/100;			
			refresh_field('e_modified_amount', tbl[i].name, 'earning_details');
		}
		total_earn += flt(tbl[i].e_modified_amount);
	}
	doc.gross_pay = total_earn + flt(doc.arrear_amount) + flt(doc.leave_encashment_amount);
	refresh_many(['e_modified_amount', 'gross_pay']);
}

// Calculate deduction total
// ------------------------------------------------------------------------
var calculate_ded_total = function(doc, dt, dn) {
	var tbl = doc.deduction_details || [];

	var total_ded = 0;
	for(var i = 0; i < tbl.length; i++){
		if(cint(tbl[i].d_depends_on_lwp) == 1) {
			tbl[i].d_modified_amount = Math.round(tbl[i].d_amount)*(flt(doc.payment_days)/cint(doc.total_days_in_month)*100)/100;
			refresh_field('d_modified_amount', tbl[i].name, 'deduction_details');
		}
		total_ded += flt(tbl[i].d_modified_amount);
	}
	doc.total_deduction = total_ded;
	refresh_field('total_deduction');	
}

// Calculate net payable amount
// ------------------------------------------------------------------------
var calculate_net_pay = function(doc, dt, dn) {
	doc.net_pay = flt(doc.gross_pay) - flt(doc.total_deduction);
	doc.rounded_total = Math.round(doc.net_pay);
	refresh_many(['net_pay', 'rounded_total']);
}

// trigger on arrear
// ------------------------------------------------------------------------
cur_frm.cscript.arrear_amount = function(doc,dt,dn){
	calculate_earning_total(doc, dt, dn);
	calculate_net_pay(doc, dt, dn);
}

// trigger on encashed amount
// ------------------------------------------------------------------------
cur_frm.cscript.leave_encashment_amount = cur_frm.cscript.arrear_amount;

// validate
// ------------------------------------------------------------------------
cur_frm.cscript.validate = function(doc, dt, dn) {
	calculate_all(doc, dt, dn);
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}		
}


