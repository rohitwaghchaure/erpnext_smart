# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
invoice_list = []

class CutOrder(Document):	
	def get_invoice_details(self, invoice_no=None):
		if not invoice_no in invoice_list:
			if not self.get('cut_order_item'):
				self.set('cut_order_item', [])
			sales_invoices = self.get_invoice(invoice_no)
			if sales_invoices:
				for si_no in sales_invoices:
					si = self.append('cut_order_item', {})
					self.create_invoice_bundle(si_no, si)
		return "Done"

	def get_invoice(self, invoice_no=None):
		cond = "1=1"
		if invoice_no:
			cond = "parent='%s'"%(invoice_no)
		return frappe.db.sql("select parent, item_code, qty from `tabSales Invoice Item` where docstatus='1' and "+cond+"",as_list=1)

	def create_invoice_bundle(self, invoice_detail, si):
		if not invoice_detail[0] in invoice_list:
			invoice_list.append(invoice_detail[0])
		si.invoice_no = invoice_detail[0]
		si.article_code = invoice_detail[1]
		si.qty = invoice_detail[2]
