# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, today
from tools.custom_data_methods import get_user_branch

class HRDailyActivities(Document):
	def get_employee(self):
		self.set('ad_details', [])
		for employye in frappe.db.sql("""select name, employee_name from tabEmployee 
				where branch = '%s' and ifnull(status,'')='Active'"""%(self.branch), as_dict=1, debug=1):
			e = self.append('ad_details', {})
			e.employee_id = employye.get('name')
			e.employee_name = employye.get('employee_name')


	def on_submit(self):
		drawings_id = []
		self.tot_drawing = 0.0
		for employee_details in self.ad_details:
			self.create_attendance_entry(employee_details)
			self.create_drawing_entry(employee_details, drawings_id)
		self.create_jv_for_drawings(drawings_id)

	def create_attendance_entry(self, employee_details):
		# employee, employee_name, status
		if employee_details.status != '':
			att = frappe.new_doc('Attendance')
			att.employee = employee_details.employee_id
			att.employee_name = employee_details.employee_name
			att.status = employee_details.status
			att.att_date = self.date
			att.branch = get_user_branch()
			att.submit()
		
	def create_drawing_entry(self, employee_details, drawings_id):
		# date, employee_id, employee_name, amount
		if employee_details.drawings:
			dwr = frappe.new_doc('Daily Drawing')
			dwr.employee_id = employee_details.employee_id
			dwr.employee_name = employee_details.employee_name
			dwr.date = self.date
			dwr.drawing_amount = employee_details.drawings
			dwr.submit()
			self.tot_drawing += flt(employee_details.drawings)
			drawings_id.append(dwr.name)

	def	create_jv_for_drawings(self, drawings_id):
		company = frappe.db.get_value('Global Defaults', None, 'default_company')

		jv = frappe.new_doc("Journal Voucher")
		jv.naming_series = 'JV-'
		jv.voucher_type = 'Journal Entry'
		jv.posting_date = today()
		jv.user_remark = "Daily Drawings: %s "%','.join(drawings_id)
		jv.save()

		jvd = frappe.new_doc("Journal Voucher Detail")
		jvd.account = frappe.db.get_value('Branch', self.branch, 'drawing_acc')
		jvd.debit = self.tot_drawing
		jvd.cost_center = frappe.db.get_value('Company', self.branch, 'cost_center')
		jvd.is_advance = 'No'
		jvd.parentfield = 'entries'
		jvd.parenttype = 'Journal Voucher'
		jvd.parent = jv.name
		jvd.save()

		jvd1 = frappe.new_doc("Journal Voucher Detail")
		jvd1.account = frappe.db.get_value('Company', company, 'default_cash_account')
		jvd1.credit = self.tot_drawing
		jvd1.cost_center = frappe.db.get_value('Branch', self.branch, 'cost_center')
		jvd1.is_advance = 'No'
		jvd1.parentfield = 'entries'
		jvd1.parenttype = 'Journal Voucher'
		jvd1.parent = jv.name
		jvd1.save()

		ujv = frappe.get_doc("Journal Voucher", jv.name)
		ujv.total_credit  = jv.total_debit = self.tot_drawing
		ujv.submit()