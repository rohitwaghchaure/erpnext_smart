# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Settlement(Document):
	def get_details(self):
		self.fill_task_details()
		self.fill_loan_details()
		self.fill_tools_details()

	def fill_tools_details(self):
		pass

	def fill_task_details(self):
		self.set('pending_task',[])
		for task in frappe.db.sql("""select distinct ed.task from `tabEmployee Details` ed, tabTask t 
				where ed.employee='%s' and ed.task is not null 
					and t.name = ed.task and t.status = 'Open'"""%(self.employee_id), as_list=1):
			e = self.append('pending_task', {})
			e.task = task[0]

	def fill_loan_details(self):
		self.set('loan_detail',[])
		for loan in frappe.db.sql("""select name ,total_loan_amount, 
					ifnull(pending_amount,0) as pending_amt, 
					total_loan_amount - ifnull(pending_amount,0) as diff 
				from tabLoan where employee_id = '%s'"""%(self.employee_id), as_dict=1):
			e = self.append('loan_detail', {})
			e.loan_id = loan.name
			e.loan_amount = loan.total_loan_amount
			e.paid_amount = loan.pending_amt
			e.remaining = loan.diff