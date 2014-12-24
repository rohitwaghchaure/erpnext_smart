# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ProductCatalog(Document):
	def get_image_view(self):
		img_path = frappe.db.get_value('File Data',{'attached_to_doctype':'Product Catalog', 'attached_to_name':self.name},'file_url')
		self.image_view = "<img src='%s'>"%(img_path)
		return "Done"

	def get_update_image_view(self, image_path):
		name = frappe.db.get_value('File Data',{'attached_to_doctype':'Product Catalog', 'attached_to_name':self.name, 'file_url':image_path}, 'name')
		if name:
			frappe.db.sql("""delete from `tabFile Data` where 
				attached_to_doctype = 'Product Catalog' and attached_to_name = '%s' and name not in('%s')"""%(self.name, name))
			self.image_view = "<img src='%s'>"%(image_path)
		return "Done"

