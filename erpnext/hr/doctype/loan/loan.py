# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

class Loan(Document):
	def calc_emi(self):
		p = flt(self.principle)
		
		if self.payment_type == 'Monthly':
			div = 12
		if self.payment_type == 'Weekly':
			div = 52

		r = flt(self.rate_of_interest)/100/div
		n = cint(self.period)

		frappe.errprint([p, r, n])
		loc_emi = ((p*r)*(r+1)**n) / (((r+1)**n) - 1)

		self.emi = loc_emi

		self.total_loan_amount = loc_emi * n

		self.pending_amount = loc_emi * n

