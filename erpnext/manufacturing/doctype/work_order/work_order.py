# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

# from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, comma_and, cint
from erpnext.accounts.accounts_custom_methods import generate_serial_no, release_work_order
from frappe.model.naming import make_autoname
from frappe import _, msgprint, throw

class WorkOrder(Document):
	def autoname(self):
		if self.work_order_no:
			self.name = self.work_order_no
		else:
			self.name = make_autoname(self.naming_series+'.#####')

	# def validate(self):
	# 	self.make_serial_no

	def on_update(self):
		self.update_process_in_production_dashboard()
		# self.update_branch_in_trials()

	def update_process_in_production_dashboard(self):
		for d in self.get('process_wise_warehouse_detail'):
			if d.warehouse:
				frappe.db.sql("""update `tabProcess Log` p, `tabProduction Dashboard Details` pd set p.branch = '%s' 
					where p.parent = pd.name and p.process_name='%s' and pd.work_order='%s' 
					and pd.sales_invoice_no='%s'"""%(d.warehouse, d.process, self.name, self.sales_invoice_no))


	def update_branch_in_trials(self):
		name = frappe.db.get_value('Work Order Distribution', {'tailor_work_order':self.name, 'tailoring_item':self.item_code}, 'trials')
		for d in self.get('process_wise_warehouse_detail'):
			if cint(d.actual_fabric) == 1 and d.warehouse and d.process:
				frappe.db.sql("update `tabTrial Dates` set trial_branch = '%s' where parent ='%s' and process ='%s'"%(d.warehouse, name, d.process))

	# def make_serial_no(self):
	# 	if not self.serial_no_data:
	# 		generate_serial_no(self.item_code,self.item_qty)

	def get_details(self, template):
		self.get_measurement_details(template)
		# self.get_process(template)
		# self.get_raw_material(template)
		return "Done"

	# def on_update(self):
	# 	item_name = frappe.db.sql("select item_name from `tabItem` where item_code='%s'"%(self.item_code))
	# 	for d in self.get('wo_process'):
	# 		task_list = frappe.db.sql("select name from `tabTask` where subject='%s'"%(d.process),as_list=1)
	# 		if not task_list:
	# 			c = frappe.new_doc('Task')
	# 			c.subject = d.process
	# 			c.process_name =d.process
	# 			c.item_name =item_name[0][0]
	# 			c.sales_order_number = self.sales_invoice_no
	# 			c.save()

	def get_measurement_details(self, template):
		self.set('measurement_item', [])
		args = frappe.db.sql("""select * from `tabMeasurement Item`
			where parent='%s'"""%(template),as_dict=1)
		if args:
			for data in args:
				mi = self.append('measurement_item', {})
				mi.parameter = data.parameter
				mi.abbreviation = data.abbreviation
				mi.image_view = data.image_view
				mi.value = data.value
				mi.default_value = data.default_value
		return "Done"

	def get_process(self, item):
		self.set('wo_process', [])
		args = frappe.db.sql("""select * from `tabProcess Item`
			where parent='%s'"""%(item),as_dict=1)
		if args:
			for data in args:
				prd = self.append('wo_process', {})
				prd.process = data.process_name
				prd.trial = data.trial
				prd.quality_check = data.quality_check
		return "Done"

	def get_raw_material(self, item):
		self.set('raw_material', [])
		args = frappe.db.sql("""select * from `tabRaw Material Item`
			where parent='%s'"""%(item),as_dict=1)
		if args:
			for data in args:
				prd = self.append('raw_material', {})
				prd.item_code = data.item
				prd.item_name = frappe.db.get_value('Item', data.item, 'item_name')
		return "Done"

	def apply_rules(self, args):
		apply_measurement_rules(self.get('measurement_item'), args)

	def on_submit(self):
		self.update_status('Completed')
		self.set_work_order()
		release_work_order(self)

	def on_cancel(self):
		self.update_status('Pending')
		self.set_to_null()

	def validate_trial_serial_no(self):
		if self.serial_no_data and not self.trial_serial_no:
			frappe.throw(_("Mandatory Field: select trial serial no").format(self.trial_serial_no))

	def update_status(self, status):
		frappe.db.sql(""" update `tabProduction Dashboard Details` 
					set work_order_status='%s'
					where sales_invoice_no='%s' and article_code='%s' 
					and work_order='%s'"""%(status,self.sales_invoice_no, self.item_code, self.name))

	def set_to_null(self):
		frappe.db.sql(""" update `tabProduction Dashboard Details` 
					set work_order=(select name from tabCustomer where 1=2)
					where sales_invoice_no='%s' and article_code='%s' 
					and work_order='%s'"""%(self.sales_invoice_no, self.item_code, self.name))

	def set_work_order(self):
		frappe.db.sql(""" update `tabProduction Dashboard Details` 
					set work_order= '%s', work_order_status ='Completed'
					where sales_invoice_no='%s' and article_code='%s' 
					"""%(self.name, self.sales_invoice_no, self.item_code))

@frappe.whitelist()
def apply_measurement_rules(measurement_details=None, param_args=None):
	result_list = []
	if isinstance(measurement_details, basestring):
		measurement_details = eval(measurement_details)
	if isinstance(param_args, basestring):
		param_args = eval(param_args)

	for d in measurement_details:
			if isinstance(d, dict):
				d = type('new_dict', (object,), d)

			measurement_formula_template = frappe.db.get_value('Item', param_args.get('item'),'measurement_formula_template')
			measurement_data = frappe.db.sql("select * from `tabMeasurement Rules` where parent='%s'"%(measurement_formula_template),as_dict=1)

			for data in measurement_data:
				if data.target_parameter == d.parameter and param_args.get('parameter') == data.parameter:
					value = (data.formula).replace('S',cstr(param_args.get('value')))
					d.value = cstr(flt(eval(value)))
					frappe.errprint(d.value)
					result_list.append({'parameter': data.target_parameter, 'value': d.value})
					
	return result_list