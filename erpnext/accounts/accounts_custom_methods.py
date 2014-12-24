# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.widgets.reportview import get_match_cond
from frappe.utils import add_days, cint, cstr, date_diff, rounded, flt, getdate, nowdate, \
	get_first_day, get_last_day,money_in_words, now
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe import msgprint, _, throw
from frappe.model.naming import make_autoname
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, get_branch_warehouse, find_next_process
from tools.tools_management.custom_methods import cut_order_generation

def create_production_process(doc, method):
	for d in doc.get('work_order_distribution'):
		process_allotment = create_process_allotment(d)
		if process_allotment:
			create_dashboard(process_allotment,d,doc)

def create_work_order(doc, data, serial_no, item_code, qty):
	wo = frappe.new_doc('Work Order')
 	wo.item_code = item_code
 	wo.customer = doc.customer
 	wo.sales_invoice_no = doc.name
 	wo.customer_name = frappe.db.get_value('Customer',wo.customer,'customer_name')
 	wo.item_qty = qty
 	wo.fabric__code = get_dummy_fabric(item_code)
 	wo.serial_no_data = serial_no
 	wo.branch = data.tailoring_warehouse
 	wo.save(ignore_permissions=True)
 	
 	create_work_order_style(data, wo.name, item_code)
 	create_work_order_measurement(data, wo.name, item_code)
 	create_process_wise_warehouse_detail(data, wo.name, item_code)
 	return wo.name

def create_work_order_style(data, wo_name, item_code):
 	if wo_name and item_code:
	 	styles = frappe.db.sql(""" select distinct style, abbreviation from `tabStyle Item` where parent = '%s'
	 		"""%(item_code),as_dict=1)
	 	if styles:
	 		for s in styles:
	 			ws = frappe.new_doc('WO Style')
	 			ws.field_name = s.style
	 			ws.abbreviation  = s.abbreviation
	 			ws.parent = wo_name
	 			ws.parentfield = 'wo_style'
	 			ws.parenttype = 'Work Order'
	 			ws.table_view = 'Right'
	 			ws.save(ignore_permissions =True)
	return True

def create_work_order_measurement(data, wo_name, item_code):
	style_parm=[]
 	if wo_name and item_code:
	 	measurements = frappe.db.sql(""" select * from `tabMeasurement Item` where parent = '%s'
	 		"""%(item_code),as_dict=1)
	 	if measurements:
	 		for s in measurements:
	 			if not s.parameter in style_parm:
		 			mi = frappe.new_doc('Measurement Item')
		 			mi.parameter = s.parameter
		 			mi.abbreviation = s.abbreviation
		 			mi.image_view = s.image_view
		 			mi.parent = wo_name
		 			mi.parentfield = 'measurement_item'
		 			mi.parenttype = 'Work Order'
		 			mi.save(ignore_permissions =True)
		 			style_parm.append(s.parameter)
	return True

def create_process_wise_warehouse_detail(data, wo_name, item_code):
	if wo_name:
		for proc_wh in frappe.db.sql("""select process_name, warehouse, idx, trials from `tabProcess Item`  
			where parent = '%s'"""%item_code,as_list=1):
			mi = frappe.new_doc('Process Wise Warehouse Detail')
 			mi.process = proc_wh[0]
 			mi.warehouse = proc_wh[1]
 			mi.idx = proc_wh[2]
 			mi.actual_fabric = cint(proc_wh[3])
 			mi.parent = wo_name
 			mi.parentfield = 'process_wise_warehouse_detail'
 			mi.parenttype = 'Work Order'
 			mi.save(ignore_permissions =True)

def create_process_allotment(data):
	process_list=[]
	i = 1
	process = frappe.db.sql(""" select distinct process_name,idx, quality_check from `tabProcess Item` where parent = '%s' order by idx asc
		"""%(data.tailoring_item),as_dict = 1)
	if process:
		for s in process:
			pa = frappe.new_doc('Process Allotment')
		 	pa.sales_invoice_no = data.parent
		 	pa.process_no = i
		 	pa.process = s.process_name
		 	pa.process_work_order = data.tailor_work_order
		 	pa.qc = cint(s.quality_check)
		 	pa.status = 'Pending'
		 	pa.item = data.tailoring_item
		 	pa.branch = frappe.db.get_value('Process Wise Warehouse Detail',{'parent':data.tailor_work_order,'process':pa.process}, 'warehouse')
		 	pa.serials_data = data.serial_no_data
		 	pa.finished_good_qty = data.tailor_qty
		 	create_material_issue(data, pa)
		 	create_trials(data, pa)
		 	pa.save(ignore_permissions=True)
		 	i= i + 1
		 	process_list.append((pa.name).encode('ascii', 'ignore'))
 	return process_list

def create_material_issue(data, obj):
 	if data.tailoring_item:
 		rm = frappe.db.sql("select * from `tabRaw Material Item` where parent='%s' and raw_process='%s'"%(data.tailoring_item, obj.process),as_dict=1)
 		if rm:
 			for s in rm:
 				d = obj.append('issue_raw_material',{})
 				d.raw_material_item_code = s.raw_item_code
 				d.raw_material_item_name = frappe.db.get_value('Item',s.raw_item_code,'item_name')
 				d.raw_sub_group = s.raw_item_sub_group or frappe.db.get_value('Item',s.raw_item_code,'item_sub_group')
 				d.uom = frappe.db.get_value('Item',s.raw_item_code,'stock_uom')
 	return True

def create_trials(data, obj):
 	if data.trials:
 		trials = frappe.db.sql("select * from `tabTrial Dates` where parent='%s' and process='%s' order by idx"%(data.trials, obj.process), as_dict=1)
 		if trials:
 			for trial in trials:
 				s = obj.append('trials_transaction',{})
				s.trial_no = trial.idx
				s.trial_date = trial.trial_date
				s.work_order = data.tailor_work_order
				s.status= 'Pending'
	return "Done"

def make_trial(data, item_code, parent):
	s= frappe.new_doc('Trials Master')
	s.sales_invoice_no = data.parent
	s.customer = frappe.db.get_value('Sales Invoice',data.parent,'customer')
	s.item_code = item_code
	s.item_name = frappe.db.get_value('Item',s.item_code,'item_name')
	s.process = parent
	s.save(ignore_permissions=True)
	return s.name

# def make_trial_transaction(data, args, trial):
# 	s = frappe.new_doc('Trials Transaction')
# 	s.trial_no = trial.trial_no
# 	s.trial_date = trial.trial_date
# 	s.work_order = data.tailor_work_order
# 	s.status= 'Pending'
# 	s.parent = args.get('parent')
# 	s.parenttype = args.get('parenttype')
# 	s.parentfield = 'trials_transaction'
# 	s.save(ignore_permissions=True)
# 	return "Done"

# def make_raw_material_entry(data, args):
# 	if args.get('type') =='invoice':
# 		raw_material = retrieve_fabric_raw_material(data, args)
# 	else:
# 		raw_material = frappe.db.sql("select raw_trial_no, raw_item_code, raw_item_sub_group from `tabRaw Material Item` where raw_process='%s' and raw_trial_no=%s and parent='%s'"%(args.get('process_name'),args.get('trial_no'),args.get('item')),as_dict=1)
# 	if raw_material:
# 		make_entry(raw_material, args)
# 	return "Done"

# def retrieve_fabric_raw_material(data, args):
# 	return frappe.db.sql("""select '', name as raw_item_code, '' from `tabItem` 
# 	where name = '%s' union  
# 	select raw_trial_no, raw_item_code, raw_item_sub_group 
# 	from `tabRaw Material Item` where parent = '%s'"""%(args.get('item'),args.get('item')), as_dict=1)

# def make_entry(raw_material, args):
# 	for d in raw_material:
# 		s = frappe.new_doc('Issue Raw Material')
# 		s.issue_trial_no = d.raw_trial_no
# 		s.raw_material_item_code = d.raw_item_code
# 		s.raw_material_item_name = frappe.db.get_value('Item',s.raw_material_item_code,'item_name')
# 		s.raw_sub_group = d.raw_item_sub_group
# 		s.parent = args.get('parent')
# 		s.parenttype = args.get('parenttype')
# 		s.parentfield = 'issue_raw_material'
# 		s.uom = frappe.db.get_value('Item',s.raw_material_item_code,'stock_uom')
# 		s.save(ignore_permissions=True)
# 		return "Done"

def create_stock_entry(doc, data):
 	ste = frappe.new_doc('Stock Entry')
 	ste.purpose_type = 'Material Receipt'
 	ste.purpose ='Material Receipt'
 	ste.branch = get_user_branch()
 	make_stock_entry_of_child(ste,data)
 	ste.save(ignore_permissions=True)
 	st = frappe.get_doc('Stock Entry', ste.name)
 	st.submit()
 	return ste.name

def make_stock_entry_of_child(obj, data):
 	if data.tailoring_item:
 		st = obj.append('mtn_details',{})
		st.t_warehouse = frappe.db.get_value('Branch',get_user_branch(),'warehouse')
		st.item_code = data.tailoring_item
		st.serial_no = data.serial_no_data
		st.item_name = frappe.db.get_value('Item', st.item_code, 'item_name')
		st.description = frappe.db.get_value('Item', st.item_code, 'description')
		st.uom = frappe.db.get_value('Item', st.item_code, 'stock_uom')
		st.conversion_factor = 1
		st.qty = data.tailor_qty or 1
		st.transfer_qty = data.tailor_qty or 1
		st.incoming_rate = 1.00
		company = frappe.db.get_value('Global Defaults', None, 'default_company')
		st.expense_account = 'Stock Adjustment - '+frappe.db.get_value('Company', company, 'abbr')
		st.cost_center = 'Main - '+frappe.db.get_value('Company', company, 'abbr')
 	return True

def create_stock(name, item_code, warehouse, warehouse_type , qty=None):
 	if item_code:
		ste = frappe.new_doc('Stock Entry Detail')
		if warehouse_type=='source':
			ste.s_warehouse = warehouse
		else:
			ste.t_warehouse = warehouse
		ste.item_code = item_code 
		ste.item_name = frappe.db.get_value('Item', ste.item_code, 'item_name')
		ste.description = frappe.db.get_value('Item', ste.item_code, 'description')
		ste.uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
		ste.conversion_factor = 1
		ste.qty = qty or 1
		ste.transfer_qty=qty or 1
		ste.parent =name
		ste.parenttype='Stock Entry'
		ste.parentfield = 'mtn_details'
		ste.save(ignore_permissions=True)
	return True

def create_dashboard(process, d ,doc):
	pd = create_production_dashboard( process, d, doc)
	if pd:
		update_pdd(d, pd, process) # add production dashboard name on trials and process allotment form

def update_pdd(args, pdd, process_list):
		if args.trials:
			cond = "pdd='%s'"%(pdd)
			set_pdd_name('Trials', cond, args.trials)
		if process_list:
			for process_allotment in process_list:
				cond = "pdd='%s', trial_dates='%s'"%(pdd, args.trials)
				set_pdd_name('Process Allotment', cond, process_allotment)

def set_pdd_name(table, cond, name):
	frappe.db.sql(""" update `tab%s` set %s where name = '%s'"""%(table, cond, name))

def create_production_dashboard( process, data, doc):
	pd = frappe.new_doc('Production Dashboard Details')
	pd.sales_invoice_no = doc.name
	pd.article_code = data.tailoring_item
	pd.tailoring_service = data.work_order_service
	pd.article_qty = data.tailor_qty
	pd.start_branch = get_user_branch()
	pd.end_branch = data.tailor_warehouse
	pd.fabric_code = data.tailor_fabric
	pd.work_order = data.tailor_work_order
	pd.dummy_fabric_code = get_dummy_fabric(data.tailoring_item)
	pd.fabric_qty = data.tailor_fabric_qty
	pd.serial_no = data.serial_no_data
	make_production_process_log(pd, process, data)
	# serial_no_log(pd, data)
	pd.save(ignore_permissions=True)
	create_stock_entry(doc, data)
	return pd.name

def get_dummy_fabric(item):
	dummy_fabric = frappe.db.sql("""select raw_item_code from `tabRaw Material Item` 
		where parent = '%s' and raw_item_code in 
		(select name from `tabItem` where item_group = 'Fabric')"""%(item), as_list=1)
	if dummy_fabric:
		return dummy_fabric[0][0]
	return ''

def make_production_process_log(obj, process_list, args):
	process_list =  "','".join(process_list)
	process = frappe.db.sql("""select a.name,a.sales_invoice_no, a.item, a.serials_data, 
		a.process, a.process_work_order, a.branch, b.trial_no, b.trial_date,
		b.work_order from `tabProcess Allotment` a left join `tabTrials Transaction` b on b.parent = a.name 
		where a.name in %s order by a.name, b.trial_no"""%("('"+process_list+"')"), as_dict=1)
	status = 'Pending'
	if process:
		for s in process:
			pl = obj.append('process_log',{})
			pl.process_data = s.name
			pl.process_name = s.process
			pl.branch = s.branch
			pl.trials = s.trial_no
			pl.status = status
			pl.pr_work_order = s.work_order or s.process_work_order

def serial_no_log(obj, data):
	sn = cstr(data.serial_no_data).split('\n')
	for s in sn:
		if s:
			sn = obj.append('production_status_detail')
			sn.item_code = data.tailoring_item
			sn.serial_no = s
			sn.branch = data.tailor_warehouse
			sn.status = 'Ready'

def delete_production_process(doc, method):
	for d in doc.get('entries'):
		production_dict = get_dict(doc.name)
		delte_doctype_data(production_dict)

def get_dict(invoice_no):
	return {'Production Dashboard Details':{'sales_invoice_no':invoice_no}}

def delte_doctype_data(production_dict):
	for doctype in production_dict:
		for field in production_dict[doctype]:
			frappe.db.sql("Delete from `tab%s` where %s = '%s'"%(doctype, field, production_dict[doctype][field]))

def validate_sales_invoice(doc, method):
	validate_work_order_assignment(doc)

def add_data_in_work_order_assignment(doc, method):
	if not doc.get('work_order_distribution'):
		doc.set('work_order_distribution',[])
	for d in doc.get('sales_invoice_items_one'):
		if not frappe.db.get_value('Work Order Distribution', {'refer_doc':d.name},'refer_doc'):
			if cint(d.check_split_qty)==1:
				split_qty = eval(d.split_qty_dict)
				for s in split_qty:
					if s:
						prepare_data_for_order(doc,d, split_qty[s]['qty'])
			else:
				prepare_data_for_order(doc, d, d.tailoring_qty)
	validate_work_order_assignment(doc)
	return "Done"

def prepare_data_for_order(doc, d, qty):
	if cint(frappe.db.get_value('Item', d.tailoring_item_code, 'is_clubbed_product')) == 1:
		sales_bom_items = frappe.db.sql("""Select * FROM `tabSales BOM Item` WHERE 
			parent ='%s' and parenttype = 'Sales Bom'"""%(d.tailoring_item_code), as_dict=1)
		for item in sales_bom_items:
			make_order(doc, d, qty, item.item_code)
	else:
		make_order(doc, d,qty, d.tailoring_item_code)

def make_order(doc, d, qty, item_code):
		e = frappe.new_doc('Work Order Distribution')
		e.tailoring_item = item_code
		e.tailor_item_name = frappe.db.get_value('Item', item_code, 'item_name')
		e.tailor_qty = qty
		e.work_order_service = d.tailoring_price_list
		e.parenttype = 'Sales Invoice'
		e.parentfield = 'work_order_distribution'
		e.parent = doc.name
		e.serial_no_data = generate_serial_no(doc, item_code, qty)
		e.tailor_fabric= d.fabric_code
		e.refer_doc = d.name
		e.tailor_fabric_qty = frappe.db.get_value('Size Item', {'parent':d.tailoring_item_code, 'size':d.tailoring_size, 'width':d.width }, 'fabric_qty')
		e.tailor_warehouse = d.tailoring_branch
		if not e.tailor_work_order:
			e.tailor_work_order = create_work_order(doc, d, e.serial_no_data, item_code, qty)
			update_serial_no_with_wo(e.serial_no_data, e.tailor_work_order)
		if not e.trials:
			e.trials = make_schedule_for_trials(doc, d, e.tailor_work_order, item_code, e.serial_no_data)
		e.save()
		return "Done"

def make_schedule_for_trials(doc, args, work_order, item_code, serial_no_data):
	s =frappe.new_doc('Trials')
	s.item_code = item_code
	s.sales_invoice = doc.name
	s.serial_no_data = serial_no_data
	s.customer = frappe.db.get_value('Sales Invoice', doc.name, 'customer')
	s.item_name = frappe.db.get_value('Item', item_code, 'item_name')
	s.work_order = work_order
	s.save(ignore_permissions=True)
	schedules_date(s.name, item_code, work_order)
	return s.name

def schedules_date(parent, item, work_order):
	trials = frappe.db.sql("select branch_dict from `tabProcess Item` where parent='%s' order by idx"%(item), as_dict=1)
	if trials:
		for t in trials:
			if t.branch_dict:
				branch_dict = eval(t.branch_dict)
				for s in range(0, len(branch_dict)):
					d = frappe.new_doc('Trial Dates')
					d.process = branch_dict.get(cstr(s)).get('process')
					d.trial_no = branch_dict.get(cstr(s)).get('trial')
					d.actual_fabric = 1 if branch_dict.get(cstr(s)).get('actual_fabric') == 'checked' else 0
					d.quality_check = 1 if branch_dict.get(cstr(s)).get('quality_check') == 'checked' else 0
					d.amend = 1 if branch_dict.get(cstr(s)).get('amended') == 'checked' else 0
					d.trial_branch = get_user_branch()
					d.idx = cstr(s + 1)
					d.parent = parent
					d.work_order = work_order
					d.parenttype = 'Trials'
					d.parentfield = 'trial_dates'
					d.save(ignore_permissions=True)
	return "Done"

def validate_work_order_assignment(doc):
	if doc.get('work_order_distribution') and doc.get('sales_invoice_items_one'):
		for d in doc.get('sales_invoice_items_one'):
			if d.tailoring_item_code and d.tailoring_qty:
				pass
				# check_work_order_assignment(doc, d.tailoring_item_code, d.tailoring_qty)

def check_work_order_assignment(doc, item_code, qty):
	count = 0
	for d in doc.get('work_order_distribution'):
		if d.tailoring_item == item_code:
			count += cint(d.tailor_qty)
	if cint(qty) !=  count:
		frappe.throw(_("Qty should be equal"))

def create_serial_no(doc, method):
	for d in doc.get('work_order_distribution'):
		if not d.serial_no_data:
			d.serial_no_data = generate_serial_no(doc,d.tailoring_item, d.tailor_qty)
			update_serial_no_with_wo(d.serial_no_data, d.tailor_work_order)

def generate_serial_no(doc, item_code, qty):
	serial_no =''
	temp_qty = qty
	while cint(qty) > 0:
		sn = frappe.new_doc('Serial No')
		sn.name = make_autoname(str(doc.name) + '/.###') 
		sn.serial_no = sn.name
		sn.process_status = 'Open'
		sn.item_code = item_code
		sn.status = 'Available'
		sn.save(ignore_permissions=True)
		if cint(temp_qty) == qty:
			serial_no = sn.name
		else:
			serial_no += '\n' + sn.name 
		qty = cint(qty) -1
	return serial_no

def update_serial_no_with_wo(serial_no_list, work_order):
	if serial_no_list and work_order:
		serial_no_list = cstr(serial_no_list).split('\n')
		for serial_no in serial_no_list:
			frappe.db.sql(""" update `tabSerial No` set work_order='%s' where
				name ='%s'"""%(work_order, serial_no))

@frappe.whitelist()
def get_process_detail(name):
	return frappe.db.sql("""select process_data, process_name, 
		ifnull(trials,'No') as trials, (select ifnull(qi_status, '') from `tabProcess Allotment`
			where name =a.process_data) as qi_status from `tabProcess Log` a
		where parent ='%s' and branch = '%s' 
		order by process_data, trials"""%(name, get_user_branch()),as_dict=1, debug=1)

def invoice_validation_method(doc, method):
	if not doc.branch:
		doc.branch = frappe.db.get_value('User', frappe.session.user, 'branch')

@frappe.whitelist()
def get_work_order_details(sales_invoice_no):
	return frappe.db.sql(""" Select name, item_code, ifnull(status, 'Pending') as release_status 
		from `tabWork Order` where sales_invoice_no='%s'"""%(sales_invoice_no), as_dict=1)

@frappe.whitelist()
def update_status(sales_invoice_no, args):
	args = eval(args)
	for s in args:
		if s.get('status') == 'Release' and frappe.db.get_value('Work Order', s.get('work_order'), 'status')!='Release':
			validate_work_order(s)
			details = open_next_branch(frappe.db.get_value('Production Dashboard Details',{'work_order': s.get('work_order')}, 'name'), 1)
			add_to_serial_no(details, s.get('work_order'))
			cut_order_generation(s.get('work_order'), sales_invoice_no)
			update_work_order_status(s.get('work_order'), s.get('status'))
			if not frappe.db.get_value('Stock Entry Detail', {'work_order': s.get('work_order'), 'docstatus':0}, 'name'):
				sn_list = frappe.db.get_value('Work Order', s.get('work_order'), 'serial_no_data')
				parent = stock_entry_for_out(s, details.branch, sn_list, frappe.db.get_value('Work Order', s.get('work_order'), 'item_qty'))
		elif s.get('status') == 'Hold' and frappe.db.get_value('Work Order Distribution', {'tailor_work_order':s.get('work_order'), 'parent': sales_invoice_no}, 'release_status') != 'Release':
			update_work_order_status(s.get('work_order'), 'Pending')
		else:
			frappe.msgprint("Work order %s is already release"%(s.get('work_order')))

def get_status(work_order):
	process = frappe.db.sql("select process_name from `tabProcess Log` where pr_work_order='%s' and idx = 1"%(work_order), as_list=1)
	if process:
		return process[0][0]

def release_work_order(doc):
	if doc.status != 'Release' and cint(frappe.db.get_value('Sales Invoice', doc.sales_invoice_no, 'release')) == 1:
		s= {'work_order': doc.name, 'status': 'Release', 'item': doc.item_code}
		details = open_next_branch(frappe.db.get_value('Production Dashboard Details',{'work_order': doc.name}, 'name'), 1)
		add_to_serial_no(details, s.get('work_order'))
		sn_list = frappe.db.get_value('Work Order', doc.name, 'serial_no_data')
		parent = stock_entry_for_out(s, details.branch, sn_list, frappe.db.get_value('Work Order', doc.name, 'item_qty'))
		update_work_order_status(doc.name, 'Release')
		cut_order_generation(doc.name, doc.sales_invoice_no)	

def add_to_serial_no(args, work_order, sn_list=None, qc=0):
	if sn_list:
		serial_no_list = sn_list
	else:
		serial_no_list = frappe.db.get_value('Work Order', work_order, 'serial_no_data')
	if serial_no_list:
		serial_no_list = cstr(serial_no_list).split('\n')
		for serial_no in serial_no_list:
			make_serial_no_log(serial_no, args, work_order, qc)

def stock_entry_for_out(args, target_branch, sn_list, qty):
	if target_branch != get_user_branch():
		parent = frappe.db.get_value('Stock Entry Detail', {'target_branch':target_branch, 'docstatus':0, 's_warehouse': get_branch_warehouse(get_user_branch())}, 'parent')
		if parent:
			obj = frappe.get_doc('Stock Entry', parent)
			stock_entry_of_child(obj, args, target_branch, sn_list, qty)
			obj.save(ignore_permissions=True)
		else:
			parent = make_StockEntry(args, target_branch, sn_list, qty)
		return parent
	else:
		return "Completed"

def make_StockEntry(args, target_branch, sn_list, qty):
	ste = frappe.new_doc('Stock Entry')
 	ste.purpose_type = 'Material Out'
 	ste.purpose ='Material Issue'
 	ste.branch = get_user_branch()
 	stock_entry_of_child(ste, args, target_branch, sn_list, qty)
 	ste.save(ignore_permissions=True)
 	return ste.name

def stock_entry_of_child(obj, args, target_branch, sn_list, qty):
	ste = obj.append('mtn_details', {})
	ste.s_warehouse = get_branch_warehouse(get_user_branch())
	ste.target_branch = target_branch
	ste.t_warehouse = get_branch_warehouse(target_branch)
	ste.qty = qty
	ste.serial_no = sn_list
	ste.incoming_rate = 1.0
	ste.conversion_factor = 1.0
	ste.work_order = args.get('work_order')
	ste.item_code = args.get('item')
	ste.item_name = frappe.db.get_value('Item', ste.item_code, 'item_name')
	ste.stock_uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
	company = frappe.db.get_value('GLobal Default', None, 'company')
	ste.expense_account = frappe.db.get_value('Company', company, 'default_expense_account')
	return "Done"

def validate_work_order(args):
	if cint(frappe.db.get_value('Work Order', args.get('work_order'), 'docstatus')) != 1:
		frappe.throw(_("You must have to submit the work order {0} for releasing").format(args.get('work_order')))

def get_target_branch(invoice_no, args):
	branch = frappe.db.sql(""" Select a.branch, a.name from `tabProcess Log` a, `tabProduction Dashboard Details` b 
		where a.parent = b.name and work_order='%s' and sales_invoice_no='%s' and a.idx=1"""%(args.get('work_order'), invoice_no))
	if branch:
		return branch[0][0], branch[0][1]

def update_work_order_status(work_order, status):
	frappe.db.sql("""update `tabWork Order` set status= '%s' 
		where name='%s'"""%(status, work_order)) 

def prepare_serial_no_list(serial_no_list, process, process_status):
	if serial_no_list:
		serial_no_list = cstr(serial_no_list).split('\n')
		for serial_no in serial_no_list:
			update_serial_no_status(serial_no, process, process_status)

def update_serial_no_status(serial_no, process, process_status):
	if process_status!='Pending':
		validate_status(serial_no, process_status)
	frappe.db.sql(""" update `tabSerial No` set process = '%s', process_status = '%s' 
		where name='%s'"""%(process, process_status, serial_no))

def get_serial_no(doctype, txt, searchfield, start, page_len, filters):
	if filters.get('trial_no'):
		return frappe.db.sql(""" select name from `tabSerial No` where name in (select
			trials_serial_no_status from `tabTrials` where work_order='%s') and warehouse='%s'
			and (select status from `tabWork Order` where name='%s') = 'Release'"""%(filters.get('work_order'), get_branch_warehouse(get_user_branch()), filters.get('work_order')))
	else:
		return frappe.db.sql(""" select name from `tabSerial No` where warehouse = '%s' and work_order='%s' 
			and (select status from `tabWork Order` where name='%s') = 'Release'"""%(get_branch_warehouse(get_user_branch()), filters.get('work_order'), filters.get('work_order')))

def validate_status(serial_no, process_status):
	mapper = {'Closed':'Open', 'Open': 'Closed'}
	data = frappe.db.get_value('Serial No', serial_no, 'process_status')
	if mapper[process_status] != data:
		frappe.throw(_("Either process is closed or last process is not completed"))

def open_next_branch(pdd, idx):
	if pdd and idx:
		return frappe.db.get_value('Process Log',{'parent':pdd, 'idx':idx}, '*')

def check_previous_is_closed(serial_no, args, work_order):
	if frappe.db.get_value('Trials', {'pdd': args.parent, 'work_order': work_order}, 'trials_serial_no_status') != serial_no:
		process = frappe.db.sql("""select process from `tabProcess Wise Warehouse Detail` where 
			parent='%s' and idx < (select idx from `tabProcess Wise Warehouse Detail` where 
			parent='%s' and process='%s') order by idx desc limit 1"""%(args.parent, args.parent, args.process_name), as_list=1)
		if process:
			serial_no_data = frappe.db.get_value('Serial No Detail', {'parent': serial_no, 'process': process[0][0]}, '*')
			if serial_no_data.status != 'Completed':
				frappe.throw(_('You have not closed previous process or trials'))
			elif cint(serial_no_data.has_qc) == 1 and qc_completed != 'Completed':
				frappe.throw(_('Quality checking is pending for previous process or trials'))
	else:
		check_previous_is_closed_for_trials(serial_no, args, work_order)

def check_previous_is_closed_for_trials(serial_no, args, work_order):
	cond = "1=1"
	if args.trials:
		cond = "trials='%s'"%(args.trials)
	process_detail = frappe.db.sql("""select process_name, trials from 
		`tabProcess Log` where parent='%s' and idx < (select idx from `tabProcess Log` 
		where parent='%s' and process_name='%s' and %s ) and skip_trial!=1 
		order by idx desc limit 1"""%(args.parent, args.parent, args.process_name, cond), as_list=1, debug=1)

	if process_detail:
		if process_detail[0][1]:
			if frappe.db.get_value('Serial No Detail', {'parent': serial_no, 'process': process_detail[0][0], 'trial_no': process_detail[0][1]}, 'status') != 'Completed':
				frappe.throw(_('You have not closed previous process or trials'))
		elif frappe.db.get_value('Serial No Detail', {'parent': serial_no, 'process': process_detail[0][0]}, 'status') != 'Completed':
			frappe.throw(_('You have not closed previous process or trials'))


def make_serial_no_log(serial_no, args, work_order, qc):
	if cint(args.idx)>1:
		check_previous_is_closed(serial_no, args, work_order)

	if args.trials:
		if not frappe.db.get_value('Serial No Detail', {'parent':serial_no, 'process': args.process_name,'trial_no': args.trials,  'work_order': work_order}, 'name'):
			make_sn_detail(serial_no, args, work_order, qc)
	elif not frappe.db.get_value('Serial No Detail', {'parent':serial_no, 'process': args.process_name, 'work_order': work_order}, 'name'):
		make_sn_detail(serial_no, args, work_order, qc)

def make_sn_detail(serial_no, args, work_order, qc):
	snd = frappe.new_doc('Serial No Detail')
	snd.process_data = args.process_data
	snd.process = args.process_name
	snd.has_qc = cint(qc)
	snd.trial_no = args.trials
	snd.work_order = work_order
	snd.parenttype = 'Serial No'
	snd.parentfield = 'serial_no_detail'
	snd.status = 'Assigned'
	snd.idx_no = args.idx
	snd.parent = serial_no
	snd.save(ignore_permissions=True)

def update_status_to_completed(serial_no, process_data, trial_no):
	cond = "1=1"
	if trial_no:
		cond = "trial_no = '%s'"%(trial_no)
	name = frappe.db.sql("""select name from `tabSerial No Detail` where parent='%s'
		and process_data='%s' and status='Assigned' and %s"""%(serial_no, process_data, cond), as_list=1)
	if name:
		update_serial_no_log_status(name[0][0], 'Completed')
	else:
		frappe.throw(_("Already completed or not assigned"))

def get_idx_for_serialNo(args, pdd, process):
	if args.tailor_process_trials:
		return frappe.db.get_value('Process Log' ,{'parent': pdd, 'process_name': process, 'trials':args.tailor_process_trials}, 'idx')
	else:
		return  frappe.db.get_value('Process Log' ,{'parent': pdd, 'process_name': process}, 'idx')

def check_for_reassigned(serial_no, args, process):
	cond = "1=1"
	if args.tailor_process_trials:
		cond = "trial_no='%s'"%(args.tailor_process_trials)

	name = frappe.db.sql("""select name from `tabSerial No Detail`
		where parent='%s' and process='%s' and status='Completed' and %s"""%(serial_no, process, cond), as_list=1)
	if name:
		update_serial_no_log_status(name[0][0], 'Assigned')
	else:
		frappe.throw(_("already completed"))

def update_serial_no_log_status(name, status):
	frappe.db.sql("Update `tabSerial No Detail` set status='%s' where name='%s'"%(status, name))


def make_stock_entry_against_qc(doc, method):
	if doc.get('qa_specification_details'):
		for data in doc.get('qa_specification_details'):
			if data.status == 'Rejected':
				frappe.throw(_('Quality checking is rejected at row {0}').format(data.idx))
			elif doc.serial_no_data:
				update_QI_for_SerialNo(doc, data)
		make_ste_for_QI(doc, data)

def update_QI_for_SerialNo(doc, data):
	sn_list = cstr(doc.serial_no_data).split('\n')
	cond = "1=1"
	if doc.process:
		cond = "process = '%s'"%(doc.process)
	elif doc.process and doc.trial_no:
		cond = "process = '%s' and trial_no='%s'"%(doc.process, doc.trial_no)
	for serial_no in sn_list:
		frappe.db.sql(""" update `tabSerial No Detail` set qc_completed='Completed' where 
			parent= '%s' and work_order='%s' and %s"""%(serial_no, doc.work_order, cond))

def make_ste_for_QI(self, data):
	details = find_next_process(self.pdd, self.process, self.trial_no)
	target_branch = get_branch(self, details)
	args = {'work_order': self.work_order, 'status': 'Release', 'item': self.item_code}
	parent = stock_entry_for_out(args, target_branch, self.serial_no_data, self.sample_size)
	if parent and self.tdd and self.trial_no:
		frappe.db.sql("""update `tabTrial Dates` set quality_check_status='Completed' where 
			parent='%s' and trial_no = '%s'"""%(self.tdd, self.trial_no))

def get_branch(self, pdlog):
	if pdlog:
		branch = pdlog.branch	
	else:
		branch = frappe.db.get_value('Production Dashboard Details', self.pdd, 'end_branch')
	if self.trial_no and self.tdd:
		branch = frappe.db.get_value('Trial Dates', {'parent': self.tdd, 'trial_no': self.trial_no}, 'trial_branch')	
	return branch

def update_QI_status(doc, method):
	msg = get_QI_status(doc)
	frappe.db.sql("""update `tabProduction Dashboard Details` set 
		qi_status='%s' where name = '%s'"""%(msg, doc.pdd))
	frappe.db.sql("""update `tabProcess Allotment` set 
		qi_status='%s' where pdd = '%s' and process = '%s'"""%(msg, doc.pdd, doc.process))

def get_QI_status(self):
	msg = 'Accepted'
	for data in self.get('qa_specification_details'):
		if d.status == 'Rejected':
			msg = 'Rejected'
	return msg
	
