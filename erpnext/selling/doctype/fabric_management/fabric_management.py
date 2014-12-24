# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import add_days, cint, cstr, date_diff, flt, getdate, nowdate, \
	get_first_day, get_last_day

from frappe import msgprint, _, throw	

class FabricManagement(Document):
	def get_invoice_details(self, invoice_no=None):
		frappe.errprint("in the get_invoice fabric_details ")
		self.set('fabric_details', [])
		sales_invoices = frappe.db.sql("""select parent,tailoring_item_code,tailoring_item_name,tailoring_qty,fabric_code,fabric_qty,cut_fabric_status from 
			`tabSales Invoice Items` where fabric_owner='Self' and cut_fabric_status='Pending'""",as_dict=1)
		frappe.errprint(sales_invoices)
		if sales_invoices:
			for inv in sales_invoices:
				si = self.append('fabric_details', {})
				si.sales_invoice = inv.parent
				si.tailoring_item_code = inv.tailoring_item_code
				si.tailoring_item_name = inv.tailoring_item_name
				si.fabric_code = inv.fabric_code
				si.fabric_qty = inv.fabric_qty
				si.quantity=inv.tailoring_qty
				si.cut_fabric_status=inv.cut_fabric_status
		return "Done"

	def cut_fabric(self):
		self.make_mat_issue()

	def make_mat_issue(self):
		fin_dict=self.make_dict()
		frappe.errprint("in the dict1")
		frappe.errprint(fin_dict['Out'])
		if fin_dict['Out']:
			st =frappe.new_doc("Stock Entry")
			st.set('mtn_details', [])
			st.purpose="Material Issue"
			self.update_stock(st,fin_dict['Out'])
			st.docstatus=0
			st.save(ignore_permissions=True)
			frappe.errprint("Done")
		else:
			frappe.msgprint(_("Please Select Any Row"))
			
	def update_stock(self,st,fin_dict):
		frappe.errprint("in the update_stock ")
		for d in fin_dict:
			frappe.errprint(d['s_warehouse'])
			e = st.append('mtn_details', {})
			e.item_code=cstr(d['item_code'])
			e.item_name=cstr(d['item_name'])
			e.item_description=cstr(d['item_description'])
			e.s_warehouse=cstr(d['s_warehouse'])
			e.expense_account=d['expense_account']
			e.buying_cost_center=d['buying_cost_center']
			e.conversion_factor=d['conversion_factor']
			e.qty=flt(d['qty'])
			e.uom=cstr(d['uom'])
			self.update_sales_invoice(d['invoice_no'])

	def update_sales_invoice(self,invoice_no):
		frappe.errprint(" in the update_sales_invoice ")
		frappe.errprint(invoice_no)
		frappe.db.sql("""Update `tabSales Invoice Items` set cut_fabric_status="Completed" where parent='%s'"""%(invoice_no),debug=1)
		return "Done"
			
	def make_dict(self):
		dict1={}
		dict1['Out']=[]
		for d in self.get('fabric_details'):
			if d.select==1:
				subdict={}
				subdict['item_code']=cstr(d.fabric_code)
				subdict['item_name']=cstr(frappe.db.get_value('Item', d.fabric_code, 'item_name'))
				subdict['item_description']=cstr(frappe.db.get_value('Item', d.fabric_code, 'description'))
				subdict['uom']= frappe.db.get_value('Item',d.fabric_code, 'stock_uom')
				subdict['s_warehouse']='Stores - I'
				subdict['expense_account']='Stock Adjustment - I'
				subdict['buying_cost_center']='Main - I'
				subdict['conversion_factor']=flt(1)
				subdict['qty']=flt(d.fabric_qty) or 1
				subdict['invoice_no']=cstr(d.sales_invoice)
				dict1['Out'].append(subdict)
		return dict1		
		

 