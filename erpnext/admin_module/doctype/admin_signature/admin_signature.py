# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, nowdate, now, cint

class AdminSignature(Document):
	def get_invoices_list(self):
		self.set('admin_note', [])
		inv = frappe.db.sql(""" select name, authenticated from `tabSales Invoice` where docstatus = 1
			and authenticated = 'Rejected' order by name desc""", as_dict=1)
		if inv:
			for s in inv:
				ad = self.append('admin_note', {})
				ad.sales_invoice = s.name
				ad.status = s.authenticated
		return "Done"

	def processed_methods(self, invoice_no=None):
		for d in self.get('admin_note'):
			if invoice_no and invoice_no == d.sales_invoice and d.status and cint(d.select) == 1:
				frappe.db.sql(""" update `tabSales Invoice` set admin_authentication_note = '%s', authenticated='%s'
					where name ='%s'"""%(d.note, d.status, d.sales_invoice))
				break
			elif d.status and cint(d.select) == 1:
				frappe.db.sql(""" update `tabSales Invoice` set admin_authentication_note = '%s', authenticated='%s'
					where name ='%s'"""%(d.note, d.status, d.sales_invoice))
		self.get_invoices_list()
		return "Done"			
