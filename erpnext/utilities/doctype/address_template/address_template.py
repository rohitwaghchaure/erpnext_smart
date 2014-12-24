# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class AddressTemplate(Document):
	def validate(self):
		defaults = frappe.db.get_values("Address Template",
			{"is_default":1, "name":("!=", self.name)})
		if not self.is_default:
			if not defaults:
				self.is_default = 1
				frappe.msgprint(_("Setting this Address Template as default as there is no other default"))
		else:
			if defaults:
				for d in defaults:
					frappe.db.set_value("Address Template", d[0], "is_default", 0)

	def on_trash(self):
		if self.is_default:
			frappe.throw(_("Default Address Template cannot be deleted"))
