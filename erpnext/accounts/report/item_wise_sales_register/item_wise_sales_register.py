# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def execute(filters=None):
	if not filters: filters = {}
	columns = get_columns()
	last_col = len(columns)

	item_list = get_items(filters)
	if item_list:
		item_tax, tax_accounts = get_tax_accounts(item_list, columns)
	
	data = []
	for d in item_list:
		row = [d.item_code, d.item_name, d.item_group, d.parent, d.posting_date, 
			d.customer_name, d.debit_to, d.territory, d.project_name, d.company, d.sales_order, 
			d.delivery_note, d.income_account, d.qty, d.base_rate, d.base_amount]
			
		for tax in tax_accounts:
			row.append(item_tax.get(d.parent, {}).get(d.item_code, {}).get(tax, 0))

		total_tax = sum(row[last_col:])
		row += [total_tax, d.base_amount + total_tax]
		
		data.append(row)
	
	return columns, data
	
def get_columns():
	return [
		"Item Code:Link/Item:120", "Item Name::120", "Item Group:Link/Item Group:100", 
		"Invoice:Link/Sales Invoice:120", "Posting Date:Date:80", "Customer:Link/Customer:120", 
		"Customer Account:Link/Account:120", "Territory:Link/Territory:80",
		"Project:Link/Project:80", "Company:Link/Company:100", "Sales Order:Link/Sales Order:100", 
		"Delivery Note:Link/Delivery Note:100", "Income Account:Link/Account:140", 
		"Qty:Float:120", "Rate:Currency:120", "Amount:Currency:120"
	]
	
def get_conditions(filters):
	conditions = ""
	
	for opts in (("company", " and company=%(company)s"),
		("account", " and si.debit_to = %(account)s"),
		("item_code", " and si_item.item_code = %(item_code)s"),
		("from_date", " and si.posting_date>=%(from_date)s"),
		("to_date", " and si.posting_date<=%(to_date)s")):
			if filters.get(opts[0]):
				conditions += opts[1]

	return conditions
		
def get_items(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql("""select si_item.parent, si.posting_date, si.debit_to, si.project_name, 
		si.customer, si.remarks, si.territory, si.company, si_item.item_code, si_item.item_name, 
		si_item.item_group, si_item.sales_order, si_item.delivery_note, si_item.income_account, 
		si_item.qty, si_item.base_rate, si_item.base_amount, si.customer_name
		from `tabSales Invoice` si, `tabSales Invoice Item` si_item 
		where si.name = si_item.parent and si.docstatus = 1 %s 
		order by si.posting_date desc, si_item.item_code desc""" % conditions, filters, as_dict=1)
		
def get_tax_accounts(item_list, columns):
	import json
	item_tax = {}
	tax_accounts = []
	
	tax_details = frappe.db.sql("""select parent, account_head, item_wise_tax_detail
		from `tabSales Taxes and Charges` where parenttype = 'Sales Invoice' 
		and docstatus = 1 and ifnull(account_head, '') != ''
		and parent in (%s)""" % ', '.join(['%s']*len(item_list)), 
		tuple([item.parent for item in item_list]))
		
	for parent, account_head, item_wise_tax_detail in tax_details:
		if account_head not in tax_accounts:
			tax_accounts.append(account_head)
				
		if item_wise_tax_detail:
			try:
				item_wise_tax_detail = json.loads(item_wise_tax_detail)
				for item, tax_amount in item_wise_tax_detail.items():
					item_tax.setdefault(parent, {}).setdefault(item, {})[account_head] = \
						 flt(tax_amount[1]) if isinstance(tax_amount, list) else flt(tax_amount)
			except ValueError:
				continue
	
	tax_accounts.sort()
	columns += [account_head + ":Currency:80" for account_head in tax_accounts]
	columns += ["Total Tax:Currency:80", "Total:Currency:80"]

	return item_tax, tax_accounts