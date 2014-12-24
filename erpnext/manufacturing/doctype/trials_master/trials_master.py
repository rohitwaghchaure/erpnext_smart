# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _, throw
from frappe.model.document import Document
from erpnext.manufacturing.doctype.process_allotment.process_allotment import create_se

class TrialsMaster(Document):
	def make_stock_entry(self):
		if self.get('issue_raw_material'):
			create_se(self.get('issue_raw_material'))

	def validate(self):
		self.create_finished_food()

	def create_finished_food(self):
		for d in self.get('trials_transaction'):
			self.check_status(d)
			if d.trial_product and d.trial_good_serial_no and d.status=='Completed' and d.good_status!='Completed':
				self.validate_serial(d)
				name = self.create_finished_goods(d)
				d.stock_entry_ref = name
				d.good_status = 'Completed'

	def check_status(self, args):
		if args.status == 'Pending' and args.good_status == 'Completed':
			frappe.throw(_("Row {0} error: It is already completed, can not change the status").format(args.idx))
		return "Done"

	def validate_serial(self, args):
		if frappe.db.get_value('Serial No',args.trial_good_serial_no,'item_code') != args.trial_product :
			frappe.throw(_("Row {0} error: Select valid serial no").format(args.idx))
		return "Done"

	def create_finished_goods(self, args):
		ste = frappe.new_doc('Stock Entry')
		ste.purpose = 'Manufacture/Repack'
		ste.refer_doctype_name = self.name
		ste.save(ignore_permissions=True)
		self.make_child_entry(args, ste.name)
		ste = frappe.get_doc('Stock Entry',ste.name)
		ste.submit()
		self.make_gs_entry(args)
		return ste.name

	def make_child_entry(self, args, name):
		frappe.errprint(["wsef",args.trial_product])
		ste = frappe.new_doc('Stock Entry Detail')
		ste.t_warehouse = 'Finished Goods - I'
		ste.item_code = args.trial_product
		ste.serial_no = args.trial_good_serial_no
		ste.uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
		ste.stock_uom = frappe.db.get_value('Item', ste.item_code, 'stock_uom')
		ste.qty = 1
		ste.parent = name
		ste.conversion_factor = 1
		ste.parenttype = 'Stock Entry'
		ste.incoming_rate = 1.00
		ste.parentfield = 'mtn_details'
		ste.expense_account = 'Stock Adjustment - I'
		ste.cost_center = 'Main - I'
		ste.transfer_qty = 1
		ste.save(ignore_permissions = True)
		return "Done"

	def make_gs_entry(self, args):
		if not frappe.db.get_value('Production Status Detail',{'item_code':args.trial_product, 'serial_no':args.trial_good_serial_no},'name'):
			parent = frappe.db.get_value('Production Dashboard Details',{'sales_invoice_no':self.sales_invoice_no,'article_code':self.item_code,'process_allotment':self.process},'name')
			if parent:
				pd = frappe.new_doc('Production Status Detail')
				pd.item_code = args.trial_product
				pd.serial_no = args.trial_good_serial_no
				pd.status = 'Ready'
				pd.parent = parent
				pd.save(ignore_permissions = True)
			if parent:
				frappe.db.sql("update `tabProduction Dashboard Details` set status='Trial', trial_no=%s where name='%s'"%(args.trial_no,parent))
		return "Done"