# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, nowdate
import frappe.defaults
from frappe.model.document import Document

class Bin(Document):
	def validate(self):
		if self.get("__islocal") or not self.stock_uom:
			self.stock_uom = frappe.db.get_value('Item', self.item_code, 'stock_uom')
				
		self.validate_mandatory()
		
		self.projected_qty = flt(self.actual_qty) + flt(self.ordered_qty) + \
		 	flt(self.indented_qty) + flt(self.planned_qty) - flt(self.reserved_qty)
		
	def validate_mandatory(self):
		qf = ['actual_qty', 'reserved_qty', 'ordered_qty', 'indented_qty']
		for f in qf:
			if (not getattr(self, f, None)) or (not self.get(f)): 
				self.set(f, 0.0)
		
	def update_stock(self, args):
		self.update_qty(args)
		
		if args.get("actual_qty"):
			from erpnext.stock.stock_ledger import update_entries_after
			
			if not args.get("posting_date"):
				args["posting_date"] = nowdate()
			
			# update valuation and qty after transaction for post dated entry
			update_entries_after({
				"item_code": self.item_code,
				"warehouse": self.warehouse,
				"posting_date": args.get("posting_date"),
				"posting_time": args.get("posting_time")
			})
			
	def update_qty(self, args):
		# update the stock values (for current quantities)
		
		self.actual_qty = flt(self.actual_qty) + flt(args.get("actual_qty"))
		self.ordered_qty = flt(self.ordered_qty) + flt(args.get("ordered_qty"))
		self.reserved_qty = flt(self.reserved_qty) + flt(args.get("reserved_qty"))
		self.indented_qty = flt(self.indented_qty) + flt(args.get("indented_qty"))
		self.planned_qty = flt(self.planned_qty) + flt(args.get("planned_qty"))
		
		self.projected_qty = flt(self.actual_qty) + flt(self.ordered_qty) + \
		 	flt(self.indented_qty) + flt(self.planned_qty) - flt(self.reserved_qty)
		
		self.save()
		
	def get_first_sle(self):
		sle = frappe.db.sql("""
			select * from `tabStock Ledger Entry`
			where item_code = %s
			and warehouse = %s
			order by timestamp(posting_date, posting_time) asc, name asc
			limit 1
		""", (self.item_code, self.warehouse), as_dict=1)
		return sle and sle[0] or None