# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cstr, flt, getdate, comma_and, nowdate, cint, now, nowtime
from erpnext.accounts.accounts_custom_methods import delte_doctype_data, prepare_serial_no_list, check_for_reassigned, update_status_to_completed, stock_entry_for_out, add_to_serial_no, get_idx_for_serialNo, open_next_branch
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, get_branch_warehouse, update_serial_no, find_next_process
import datetime

class ProcessAllotment(Document):

	def validate(self):
		# self.assign_task()
		# self.update_process_status()
		self.prepare_for_time_log()
		self.update_task()
		# self.make_auto_ste()
		# self.auto_ste_for_trials()
		

	def show_trials_details(self):
		trials_data = frappe.db.sql("select * from `tabProcess Log` where (ifnull(status,'') = 'Open' or ifnull(status,'')='Closed') and process_name='%s' and process_data = '%s' and trials is not null order by trials"%(self.process, self.name), as_dict=1)
		self.set('trials_transaction', [])
		for data in trials_data:
			td = self.append('trials_transaction', {})
			td.trial_no = data.trials
			td.status = data.status
			td.work_order = data.pr_work_order

	def prepare_for_time_log(self):
		if self.get('employee_details'):
			for data in self.get('employee_details'):
				self.validate_trials(data)
				self.start_process_for_serialNo(data)
				if cint(data.idx) == cint(len(self.get('employee_details'))):
					status = 'Closed' if data.employee_status == 'Completed' else 'Open'
					frappe.db.sql("update `tabTask` set status ='%s' where name='%s'"%( status, data.tailor_task))
				if data.employee_status =='Completed' and not data.time_log_name:
					name = self.make_time_log(data)
					data.time_log_name = name

	def make_time_log(self, data):
		tl = frappe.new_doc('Time Log')
		tl.from_time = data.tailor_from_time
		tl.hours = flt(data.work_completed_time)/60
		tl.to_time = datetime.datetime.strptime(tl.from_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours = flt(tl.hours))
		tl.activity_type = self.process
		tl.task = data.tailor_task
		tl.project = self.sales_invoice_no
		tl.save(ignore_permissions=True)
		t = frappe.get_doc('Time Log', tl.name)
		t.submit()
		return tl.name

	def start_process_for_serialNo(self, data):
		if data.employee_status == 'Assigned':
			idx = get_idx_for_serialNo(data, self.pdd, self.process)
			details = open_next_branch(self.pdd, idx)
			add_to_serial_no(details, self.process_work_order, data.tailor_serial_no, data.qc_required)
		else:
			self.update_sn_status(data)
			if data.employee_status == 'Completed' and not data.ste_no:
				details = find_next_process(self.pdd, self.process, data.tailor_process_trials)
				if cint(data.qc_required)==1:
					if data.tailor_process_trials and cint(frappe.db.get_value('Trial Dates',{'parent':self.trial_dates, 'trial_no':data.tailor_process_trials}, 'quality_check')) != 1:
						data.ste_no = self.make_ste(details, data)
					else:
						data.ste_no = self.make_qc(details, data)
				else:
					data.ste_no = self.make_ste(details, data)

	def make_qc(self, details, data):
		sn_list = self.get_not_added_sn(data.tailor_serial_no, 'serial_no_data', 'Quality Inspection')
		if sn_list:
			qi = frappe.new_doc('Quality Inspection')
			qi.inspection_type = 'In Process'
			qi.report_date = nowdate()
			qi.item_code = self.item
			qi.inspected_by = frappe.session.user
			qi.sample_size = data.assigned_work_qty
			qi.serial_no_data = sn_list
			qi.process = self.process
			qi.work_order = self.process_work_order
			qi.pdd = self.pdd
			qi.trial_no = data.tailor_process_trials
			qi.tdd = self.trial_dates
			self.qa_specification_details(qi)
			qi.save(ignore_permissions=True)
			return qi.name

	def qa_specification_details(self, obj):
		qi_data = frappe.db.sql("""select * from `tabItem Quality Inspection Parameter`
			where parent='%s' and qi_process='%s'"""%(self.item, self.process), as_dict=1)
		if qi_data:
			for data in qi_data:
				qa = obj.append('qa_specification_details')
				qa.process = data.process
				qa.specification = data.specification
		return "Done"

	def make_ste(self, details, data):
		s= {'work_order': self.process_work_order, 'status': 'Release', 'item': self.item}
		sn_list = self.get_not_added_sn(data.tailor_serial_no, 'serial_no', 'Stock Entry Detail')
		if sn_list:
			branch = self.get_branch(details, data)
			dte_no = stock_entry_for_out(s, branch, sn_list, data.assigned_work_qty)
			return dte_no

	def get_branch(self, pdlog, args):
		if pdlog:
			frappe.errprint('in pdlog')
			branch = pdlog.branch
		else:
			branch = frappe.db.get_value('Production Dashboard Details', self.pdd, 'end_branch')

		if args.tailor_process_trials and self.trial_dates: 
			branch = frappe.db.get_value('Trial Dates', {'parent': self.trial_dates, 'trial_no': args.tailor_process_trials}, 'trial_branch')

		return branch

	def get_not_added_sn(self, sn_list, fieldname, table):
		new_sn_list = ''
		data = frappe.db.sql(""" select %s from `tab%s` where 
			work_order = '%s' and docstatus=0"""%(fieldname, table, self.process_work_order), as_list=1)
		if data:
			for sn in data:
				sn = cstr(sn[0]).split('\n')
				for s in sn:
					if s:
						serial_no = self.check_available(s, sn_list)
						if new_sn_list:
							new_sn_list = new_sn_list + '\n' + serial_no
						else:
							new_sn_list = serial_no
		else:
			new_sn_list = sn_list
		return new_sn_list

	def check_available(self, serial_no, sn_list):
		sn_data = ''
		sn_list = cstr(sn_list).split('\n')
		for sn in sn_list:
			if sn and sn != serial_no:
				if sn_data:
					sn_data = sn_data + '\n' + sn
				else:
					sn_data = sn
		return sn_data

	def update_sn_status(self, args):
		if args.tailor_serial_no:
			serial_no_list = cstr(args.tailor_serial_no).split('\n')
			for serial_no in serial_no_list:
				if args.employee_status == 'Completed' and not args.ste_no:
					update_status_to_completed(serial_no, self.name, args.tailor_process_trials)
				elif args.employee_status == 'Reassigned':
					check_for_reassigned(serial_no, args, self.process)

	def validate_trials(self, args):
		if self.process_trials and cint(args.assigned_work_qty) > 1:
			frappe.throw(_("Only one serial no is allocated for trial no"))
		if args.employee_status == 'Completed' and args.tailor_process_trials:
			details = frappe.db.sql("""select name, production_status from `tabTrial Dates` where
				parent='%s' and trial_no='%s'"""%(self.trial_dates, args.tailor_process_trials), as_list=1)
			if details:
				if details[0][1] != 'Closed':
					frappe.db.sql(""" update `tabTrial Dates` set production_status='Closed'
						where name='%s'	"""%(details[0][0]))

	# def make_auto_ste(self):
	# 	if self.process_status == 'Closed':
	# 		self.validate_trials_closed()
	# 		cond = "1=1"
	# 		current_name, next_name = self.get_details(cond)
	# 		target_branch = frappe.db.get_value('Process Log', next_name, 'branch')
	# 		args = {'qty': self.finished_good_qty, 'serial_data': self.serials_data, 'work_order': self.process_work_order, 'item': self.item}
	# 		if get_user_branch() == target_branch:
	# 			self.update_status(current_name, next_name)
	# 			frappe.db.sql("""update `tabProcess Log` set status = 'Open' where name='%s' and trials is null"""%(next_name))
	# 		else:
	# 			parent = self.prepare_stock_entry_for_process(target_branch, args)
	# 			if parent:
	# 				self.update_status(current_name, next_name)
	# 				frappe.msgprint("Created Stock Entry %s"%(parent))
		
	# def validate_trials_closed(self):
	# 	count = frappe.db.sql("select ifnull(count(*),0) from `tabProcess Log` where process_data = '%s' and status = 'Open' and trials is not null"%(self.name), debug=1)
	# 	if count:
	# 		if cint(count[0][0])!=0	and self.process_status == 'Closed':
	# 			frappe.throw(_("You must have to closed all trials"))	

	# def update_status(self, current_name, next_name):
	# 	frappe.db.sql("""update `tabProcess Log` set status = 'Closed' where name='%s'"""%(current_name))

	# def prepare_stock_entry_for_process(self, target_branch, args):
	# 	if self.branch != target_branch and not frappe.db.get_value('Stock Entry Detail', {'work_order': self.process_work_order, 'target_branch':target_branch, 'docstatus':0, 's_warehouse': get_branch_warehouse(self.branch)}, 'name'):
	# 		parent = frappe.db.get_value('Stock Entry Detail', {'target_branch':target_branch, 'docstatus':0, 's_warehouse': get_branch_warehouse(self.branch)}, 'parent')			
	# 		if parent:
	# 			st = frappe.get_doc('Stock Entry', parent)
	# 			self.stock_entry_of_child(st, args, target_branch)
	# 			st.save(ignore_permissions= True)
	# 		else:
	# 			parent = self.make_stock_entry(target_branch, args)
	# 		frappe.msgprint(parent)
	# 		return parent

	# def auto_ste_for_trials(self):
	# 	for d in self.get('employee_details'):
	# 		cond = "1=1"
	# 		self.update_serial_no_status(d)
	# 		status = frappe.db.get_value('Process Log', {'process_data': self.name, 'trials': d.tailor_process_trials}, 'status')
	# 		if d.employee_status == 'Completed' and not d.ste_no and status!='Closed':
	# 			if d.tailor_process_trials:
	# 				cond = "trials ='%s'"%(d.tailor_process_trials)
	# 			current_name, next_name = self.get_details(cond)
	# 			target_branch = self.get_target_branch(d, next_name)

	# 			args = {'qty': d.assigned_work_qty, 'serial_data': d.tailor_serial_no, 'work_order': self.process_work_order, 'item': self.item}
	# 			d.ste_no = self.prepare_stock_entry_for_process(target_branch, args)
	# 			self.update_status(current_name, next_name)
	# 			if d.tailor_process_trials:
	# 				# trial_name = frappe.db.get_value('Trials',{'sales_invoice': self.sales_invoice_no, 'work_order': self.process_work_order, 'trial_no': d.tailor_process_trials}, 'name')
	# 				parent = frappe.db.sql(""" select name from `tabTrials` where sales_invoice='%s' and work_order='%s'"""%(self.sales_invoice_no, self.process_work_order), as_list=1)
	# 				if parent:
	# 					frappe.db.sql("""update `tabTrial Dates` set production_status = 'Closed' where
	# 						parent = '%s' and trial_no = '%s'"""%(parent[0][0], d.tailor_process_trials))

	# def get_target_branch(self, args, next_name):
	# 	if args.tailor_process_trials:
	# 		trial_name = frappe.db.get_value('Trials',{'sales_invoice': self.sales_invoice_no, 'work_order': self.process_work_order}, 'name')
	# 		trials = frappe.db.get_value('Trial Dates', {'parent': trial_name, 'process': self.process, 'trial_no': args.tailor_process_trials}, '*')
	# 		return trials.trial_branch
	# 	else:
	# 		return frappe.db.get_value('Process Log', next_name, 'branch')

	# def update_serial_no_status(self, args):
	# 	if args.tailor_serial_no:
	# 		serial_no = cstr(args.tailor_serial_no).split('\n')
	# 		for sn in serial_no:
	# 			msg = self.process + ' ' + self.emp_status
	# 			parent = frappe.db.get_value('Process Log', {'process_data': self.name}, 'parent')
	# 			update_serial_no(parent, sn, msg)

	def find_start_time(self):
		self.start_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		return "Done"

	def find_to_time(self, date_type=None):
		import math
		if not date_type:
			self.end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		if self.start_date and self.end_date:
			after = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S') 
			before = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')
			self.completed_time = cstr(math.floor(((after - before).seconds) / 60))
		else:
			frappe.msgprint("Start Date is not mentioned")
		return "Done"

	# def make_stock_entry(self, t_branch, args):
	# 	ste = frappe.new_doc('Stock Entry')
	# 	ste.purpose_type = 'Material Out'
	# 	ste.purpose ='Material Issue'
	# 	self.stock_entry_of_child(ste, args, t_branch)
	# 	ste.branch = get_user_branch()
	# 	ste.save(ignore_permissions=True)
	# 	return ste.name

	# def stock_entry_of_child(self, obj, args, target_branch):
	# 	ste = obj.append('mtn_details', {})
	# 	ste.s_warehouse = get_branch_warehouse(self.branch)
	# 	ste.target_branch = target_branch
	# 	ste.t_warehouse = get_branch_warehouse(target_branch)
	# 	ste.qty = args.get('qty')
	# 	ste.serial_no = args.get('serial_data')
	# 	ste.incoming_rate = 1.0
	# 	ste.conversion_factor = 1.0
	# 	ste.work_order = args.get('work_order')
	# 	ste.item_code = args.get('item')
	# 	ste.item_name = frappe.db.get_value('Item', ste.item_code, 'item_name')
	# 	ste.stock_uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
	# 	company = frappe.db.get_value('GLobal Default', None, 'company')
	# 	ste.expense_account = frappe.db.get_value('Company', company, 'default_expense_account')
	# 	return "Done"

	# def get_details(self , cond):
	# 	name = frappe.db.sql("""SELECT ifnull(foo.name, '') AS current_name,  (SELECT  ifnull(name, '') FROM `tabProcess Log` 
	# 							WHERE name > foo.name AND parent = foo.parent order by process_data, trials limit 1) AS next_name
	# 							FROM ( SELECT  name, parent  FROM  `tabProcess Log` WHERE   branch = '%s' 
	# 							and status != 'Closed' and process_data = '%s' and %s ORDER BY idx limit 1) AS foo """%(self.branch, self.name, cond), as_dict=1, debug=1)
	# 	if name:
	# 		return name[0].current_name, name[0].next_name
	# 	else:
	# 		'',''

	def update_task(self):
		if self.emp_status=='Assigned' and not self.get("__islocal") and self.process_tailor:
			self.task = self.create_task()
			self.update_work_order()
			if self.get('employee_details'):
				for d in self.get('employee_details'):
					if not d.tailor_task:
						d.tailor_task = self.task

	def update_work_order(self):
		if self.process_trials:
			fabric = ''
			data = frappe.db.sql(""" select a.work_order as work_order, ifnull(a.actual_fabric, '') as actual_fabric, b.pdd as pdd from `tabTrial Dates` a, `tabTrials` b where a.parent= b.name 
									 and b.work_order ='%s' and process = '%s' and trial_no = '%s'"""%(self.process_work_order, self.process, self.process_trials), as_dict=1)
			if data:
				for d in data:
					if cint(d.actual_fabric) == 1:
						fabric = frappe.db.get_value('Production Dashboard Details', d.pdd, 'fabric_code')
					else:
						fabric = frappe.db.get_value('Production Dashboard Details', d.pdd, 'dummy_fabric_code')
					if fabric:
						frappe.db.sql(""" update `tabWork Order` set fabric__code = '%s' and trial_no = '%s'
							where name = '%s'"""%(fabric, self.process_trials, d.work_order))			

	def create_task(self):
		self.validate_dates()
		tsk = frappe.new_doc('Task')
		tsk.subject = 'Do process %s for item %s'%(self.process, frappe.db.get_value('Item',self.item,'item_name'))
		tsk.project = self.sales_invoice_no
		tsk.exp_start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S').date()
		tsk.exp_end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S').date()
		tsk.status = 'Open'
		tsk.process_name = self.process
		tsk.item_code = self.item
		tsk.sales_order_number = self.sales_invoice_no
		tsk.save(ignore_permissions=True)
		return tsk.name

	# def assigned_to_user(self, data):
	# 	todo = frappe.new_doc('ToDo')
	# 	todo.description = data.task_details or 'Do process %s for item %s'%(data.process, frappe.db.get_value('Item',self.item,'item_name'))
	# 	todo.reference_type = 'Task'
	# 	todo.reference_name = data.task
	# 	todo.owner = data.user
	# 	todo.save(ignore_permissions=True)
	# 	return todo.name

	# def validate_process(self, index):
	# 	for data in self.get('wo_process'):
	# 		if cint(data.idx)<index:
	# 			if data.status == 'Pending' and cint(data.skip)!=1:
	# 				frappe.throw(_("Previous Process is Pending, please check row {0} ").format(cint(data.idx)))

	# def on_submit(self):
	# 	self.check_status()
	# 	self.change_status('Completed')
	# 	# self.make_stock_entry_for_finished_goods()

	# def check_status(self):
	# 	for d in self.get('wo_process'):
	# 		if d.status =='Pending' and cint(d.skip)!=1:
	# 			frappe.throw(_("Process is Pending, please check row {0} ").format(cint(d.idx)))

	# def on_cancel(self):
	# 	self.change_status('Pending')
	# 	self.set_to_null()
	# 	self.delete_dependecy()
	
	# def change_status(self,status):
	# 	frappe.db.sql(""" update `tabProduction Dashboard Details` 
	# 				set process_status='%s' 
	# 				where sales_invoice_no='%s' and article_code='%s' 
	# 				and process_allotment='%s'"""%(status, self.sales_invoice_no, self.item, self.name))

	# def set_to_null(self):
	# 	frappe.db.sql(""" update `tabProduction Dashboard Details` 
	# 				set process_allotment= (select name from tabCustomer where 1=2) 
	# 				where sales_invoice_no='%s' and article_code='%s' 
	# 				and process_allotment='%s'"""%( self.sales_invoice_no, self.item, self.name))

	# def delete_dependecy(self):
	# 	for d in self.get('wo_process'):
	# 		if d.task and d.user:
	# 			frappe.db.sql("delete from `tabToDo` where reference_type='%s' and owner='%s'"%(d.task, d.user))
	# 			production_dict = self.get_dict(d.task, d.user)
	# 			delte_doctype_data(production_dict)

	# def get_dict(self, task, user):
	# 	return {'Task':{'name':task}}

	# def on_status_trigger_method(self, args):
	# 	self.set_completion_date(args)
	# 	self.update_process_status(args)

	# def set_completion_date(self, args):
	# 	for d in self.get('wo_process'):
	# 		if cint(d.idx) == cint(args.idx) and d.status == 'Completed':
	# 			d.completion_date = cstr(nowdate())
	# 		else:
	# 			d.completion_date = ''
	# 	return True

	# def make_stock_entry(self):
	# 	if self.get('issue_raw_material'):
	# 		create_se(self.get('issue_raw_material'))

	# def make_stock_entry_for_finished_goods(self):
	# 	ste = frappe.new_doc('Stock Entry')
	# 	ste.purpose = 'Manufacture/Repack'
	# 	ste.branch = get_user_branch()
	# 	ste.save(ignore_permissions=True)
	# 	self.make_child_entry(ste.name)
	# 	ste = frappe.get_doc('Stock Entry',ste.name)
	# 	ste.submit()
	# 	self.make_gs_entry()
	# 	return ste.name

	# def make_child_entry(self, name):
	# 	ste = frappe.new_doc('Stock Entry Detail')
	# 	ste.t_warehouse = 'Finished Goods - I'
	# 	ste.item_code = self.item
	# 	ste.serial_no = self.serials_data
	# 	ste.qty = self.finished_good_qty
	# 	ste.parent = name
	# 	ste.conversion_factor = 1
	# 	ste.has_trials = 'No'
	# 	ste.parenttype = 'Stock Entry'
	# 	ste.uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
	# 	ste.stock_uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
	# 	ste.incoming_rate = 1.00
	# 	ste.parentfield = 'mtn_details'
	# 	ste.expense_account = 'Stock Adjustment - I'
	# 	ste.cost_center = 'Main - I'
	# 	ste.transfer_qty = self.finished_good_qty
	# 	ste.save(ignore_permissions = True)
	# 	return "Done"

	# def make_gs_entry(self):
	# 	if self.serials_data:
	# 		parent = frappe.db.get_value('Production Dashboard Details',{'sales_invoice_no':self.sales_invoice_no,'article_code':self.item,'process_allotment':self.name},'name')
	# 		sn = cstr(self.serials_data).splitlines()
	# 		for s in sn:
	# 			if not frappe.db.get_value('Production Status Detail',{'item_code':self.item, 'serial_no':s[0]},'name'):
	# 				if parent:
	# 					pd = frappe.new_doc('Production Status Detail')
	# 					pd.item_code = self.item
	# 					pd.serial_no = s
	# 					pd.status = 'Ready'
	# 					pd.parent = parent
	# 					pd.save(ignore_permissions = True)
	# 		if parent:
	# 			frappe.db.sql("update `tabProduction Dashboard Details` set status='Completed', trial_no=0 where name='%s'"%(parent))
	# 	return "Done"

	# def update_process_status(self, args=None):
	# 	self.update_parent_status()
	# 	self.update_child_status()

	# def update_parent_status(self):
	# 	if self.process_status_changes=='Yes':
	# 		cond = "a.parent=b.name and a.process_data='%s' and a.process_name='%s' and b.sales_invoice_no='%s'"%(self.name, self.process, self.sales_invoice_no)
	# 		frappe.db.sql("update `tabProcess Log` a, `tabProduction Dashboard Details` b set a.status='%s' where %s"%(self.process_status,cond))
	# 		if self.process_status=='Closed':
	# 			self.open_next_status(cond)
	# 		self.process_status_changes='No'
		
	# def update_child_status(self):
	# 	for s in self.get('trials_transaction'):
	# 		if s.trial_change_status=='Yes':
	# 			cond = "a.parent=b.name and a.process_data='%s' and a.process_name='%s' and a.trials='%s' and b.sales_invoice_no='%s'"%(self.name, self.process, s.trial_no, self.sales_invoice_no)
	# 			frappe.db.sql("update `tabProcess Log` a, `tabProduction Dashboard Details` b set a.status='%s' where %s"%(s.status, cond))
	# 			if s.status=='Closed':
	# 				self.open_next_status(cond)
	# 			s.trial_change_status='No'

	# def open_next_status(self, cond):
	# 	name = frappe.db.sql("""select a.* from `tabProcess Log` a, `tabProduction Dashboard Details` b where %s """%(cond), as_dict=1)
	# 	if name:
	# 		for s in name:
	# 			frappe.db.sql("update `tabProcess Log` set status='Open' where idx=%s and parent='%s'"%(cint(s.idx)+1, s.parent))

	def assign_task_to_employee(self):
		emp = self.append('employee_details',{})
		emp.employee = self.process_tailor
		emp.employee_name = frappe.db.get_value('Employee', self.process_tailor, 'employee_name')
		emp.tailor_task = self.task
		emp.employee_status = self.emp_status
		emp.tailor_payment = self.payment
		emp.tailor_wages = self.wages
		emp.tailor_process_trials = self.process_trials
		emp.tailor_extra_wages = self.extra_charge
		emp.tailor_extra_amt = self.extra_charge_amount
		emp.tailor_from_time = self.start_date
		emp.work_estimated_time = self.estimated_time
		emp.work_completed_time = self.completed_time
		emp.assigned_work_qty = self.work_qty
		emp.deduct_late_work = self.deduct_late_work
		emp.latework = self.latework
		emp.tailor_serial_no = self.serial_no_data
		emp.cost = self.cost
		emp.qc_required = cint(self.qc)
		return "Done"

	def calculate_estimates_time(self):
		if self.work_qty and self.start_date:
			self.estimated_time = cint(self.work_qty) * cint(frappe.db.get_value('EmployeeSkill',{'parent':self.process_tailor, 'process':self.process, 'item_code': self.item},'time'))
			self.end_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes = cint(self.estimated_time))
		return "Done"

	def calculate_wages(self):
		self.wages = 0.0
		if self.payment == 'Yes':
			self.wages = cint(self.work_qty) * cint(frappe.db.get_value('EmployeeSkill',{'parent':self.process_tailor, 'process':self.process, 'item_code': self.item},'cost'))

	def calc_late_work_amt(self):
		self.cost = flt(self.latework) * flt(frappe.db.get_value('Item',self.item,"late_work_cost"))
		return "Done"

	def validate_dates(self):
		if not self.start_date and not self.end_date:
			frappe.throw(_('Start and End Date is necessary to create task'))

	def get_trial_serial_no(self):
		get_trials = frappe.db.get_value('Trials', {'work_order':self.process_work_order}, '*')
		self.serial_no_data = get_trials.trials_serial_no_status
		self.work_qty = 1
		return "Done"

def create_se(raw_material):
	count = 0
	se = frappe.new_doc('Stock Entry')
	se.naming_series = 'STE-'
	se.purpose = 'Material Issue'
	se.posting_date = nowdate()
	se.posting_time = nowtime().split('.')[0]
	se.company = frappe.db.get_value("Global Defaults", None, 'default_company')
	se.fiscal_year = frappe.db.get_value("Global Defaults", None, 'current_fiscal_year')
	se.save()
	for item in raw_material:
		if cint(item.selected) == 1 and item.status!='Completed':
			sed = frappe.new_doc('Stock Entry Detail')
			sed.s_warehouse = get_warehouse()
			sed.parentfield = 'mtn_details'
			sed.parenttype = 'Stock Entry'
			sed.item_code = item.raw_material_item_code
			sed.item_name = frappe.db.get_value("Item", item.raw_material_item_code, 'item_name')
			sed.description = frappe.db.get_value("Item", item.raw_material_item_code, 'description')
			sed.stock_uom = item.uom
			sed.uom = item.uom
			sed.conversion_factor = 1
			sed.incoming_rate = 0.0
			sed.qty = flt(item.qty)
			sed.transfer_qty = flt(item.qty) * 1
			sed.serial_no = item.serial_no
			sed.parent = se.name
			sed.save()
			frappe.db.sql("update `tabIssue Raw Material` set status = 'Completed', selected=1 where name = '%s'"%(item.name))
			frappe.db.sql("commit")
			count += 1
	if count == 0:
		frappe.db.sql("delete from `tabStock Entry` where name = '%s'"%se.name)
		frappe.db.sql("update tabSeries set current = current-1 where name = 'STE-'")
		frappe.db.sql("commit")
	else:
		frappe.msgprint("Material Issue Stock Entry %s has been created for above items"%se.name)

def get_warehouse():
	return "Finished Goods - I"
	# warehouse = frappe.db.sql(""" select b.warehouse from tabBranch b, tabEmployee e 
	# 	where b.name = e.branch and e.user_id = '%s'"""%(frappe.session.user))

	# return ((len(warehouse[0]) > 1 ) and warehouse[0] or warehouse[0][0]) if warehouse else None