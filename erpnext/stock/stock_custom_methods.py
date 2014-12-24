# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.widgets.reportview import get_match_cond
from frappe.utils import add_days, cint, cstr, date_diff, rounded, flt, getdate, nowdate, \
	get_first_day, get_last_day,money_in_words, now
from frappe import _
from tools.custom_data_methods import generate_barcode
from frappe.model.db_query import DatabaseQuery
from tools.custom_data_methods import get_user_branch, get_branch_cost_center, update_serial_no

def update_status(doc, method):
	change_stock_entry_status(doc, 'Completed')

def change_stock_entry_status(doc, status):
	frappe.db.sql(""" update `tabProduction Dashboard Details` 
					set rm_status='%s', cut_order_status='%s'
					where stock_entry='%s'"""%(status, status ,doc.name))

def cancel_status(doc, method):
	change_stock_entry_status(doc, 'Pending')
	# set_to_null(doc)

def set_to_null(self):
	frappe.db.sql(""" update `tabProduction Dashboard Details` 
				set stock_entry=(select name from tabCustomer where 1=2)
				where sales_invoice_no='%s' and article_code='%s' 
				and work_order='%s'"""%(self.sales_invoice_no, self.item_code, self.name))

def stock_out_entry(doc, method):
	if doc.purpose_type == 'Material Out':
		in_entry  = make_stock_entry_for_in(doc)
	elif doc.purpose_type == 'Material In':
		open_process(doc)

def make_stock_entry_for_in(doc):
	branch_list = {}
	for s in doc.get('mtn_details'):
		if branch_list and branch_list.get(s.target_branch):
			make_stock_entry_for_child(s, branch_list[s.target_branch])
		else:
			name = make_stock_entry(doc, s.target_branch)
			make_stock_entry_for_child(s, name)
		branch_list.setdefault(s.target_branch, name)
	return name

def make_stock_entry(doc, target_branch):
	se = frappe.new_doc('Stock Entry')
	se.purpose_type = 'Material In'
	se.purpose = 'Material Receipt'
	se.stock_in = doc.name
	se.branch = target_branch
	se.save(ignore_permissions=True)
	return se.name

def make_stock_entry_for_child(s, name):
	sed = frappe.new_doc('Stock Entry Detail')
	sed.item_code = s.item_code
	sed.t_warehouse = frappe.db.get_value('Branches', s.target_branch, 'warehouse')
	sed.source_warehouse = s.s_warehouse
	sed.item_name = s.item_name
	sed.description = s.description
	sed.qty = s.qty
	sed.conversion_factor = s.conversion_factor
	sed.work_order = s.work_order
	sed.uom = s.uom
	sed.incoming_rate = s.incoming_rate
	sed.serial_no = s.serial_no
	sed.batch_no = s.batch_no
	sed.expense_account = s.expense_account
	sed.cost_center = s.cost_center
	sed.transfer_qty = s.transfer_qty
	sed.parenttype = s.parenttype
	sed.parentfield = s.parentfield
	sed.parent = name
	sed.save(ignore_permissions=True)
	return "Done"

def open_process(doc):
	for d in doc.get('mtn_details'):
		if d.work_order and d.has_trials!='Yes':
			if d.trials:
				frappe.db.sql(""" update `tabProcess Log` a, `tabProduction Dashboard Details` b set a.status = 'Open'
					where b.work_order = '%s' and a.branch = '%s' and a.trials ='%s' and a.status = 'Pending'"""%(d.work_order, get_user_branch(), d.trials))
			else:		
				name = frappe.db.get_value('Production Dashboard Details', {'work_order': d.work_order}, '*')
				if d.serial_no == name.serial_no:
					process = frappe.db.sql(""" select p.process_name from `tabProcess Log` p, `tabProduction Dashboard Details` pd where pd.work_order = '%s' AND p.branch= '%s'
						AND p.status='Pending' and p.parent = pd.name order by p.idx limit 1"""%(d.work_order,get_user_branch()), as_list=1)
					frappe.db.sql(""" update  `tabProcess Log` p inner join 
						`tabProduction Dashboard Details` d on p.parent=d.name inner join 
						(select parent,min(idx) as idx from  `tabProcess Log` pd where  status='Pending'
						and branch='%s' group by parent )foo on p.parent=foo.parent and p.idx=foo.idx
						set p.status='Open' WHERE  d.work_order = '%s' AND p.branch= '%s' AND p.status='Pending'"""%(get_user_branch(), d.work_order, get_user_branch()))
					if process:
						parent = frappe.db.get_value('Production Dashboard Details',{'work_order':d.work_order}, 'name')
						update_serial_no_status(process[0][0], parent, d.serial_no)

def update_serial_no_status(process, parent, serial_no):
	serial_no = cstr(serial_no).split('\n')
	for s in serial_no:
		msg = "Ready For " + process
		update_serial_no(parent, s, msg)
				

def in_stock_entry(doc, method):
	pass

@frappe.whitelist()
def get_details(item_name):
	return frappe.db.sql("""select file_url,attached_to_name from `tabFile Data` 
		where attached_to_name ='%s'"""%(item_name),as_list=1)

def item_validate_methods(doc, method):
	if doc.item_group == 'Tailoring':
		manage_price_list_for_tailoring(doc)
	else:
		make_price_list_for_merchandise(doc)
	make_sales_bom(doc)

def manage_price_list_for_tailoring(doc):
	parent_list = []
	for d in doc.get('costing_item'):
		parent = frappe.db.get_value('Item Price', {'item_code':doc.name, 'price_list':doc.service},'name')
		if not parent:
			parent = make_item_price(doc.name, doc.service)
		parent_list.append(parent.encode('ascii', 'ignore'))
		update_item_price(parent, d)
		# delete_non_present_entry(parent_list, d)
		# update_price_list(d)

def make_price_list_for_merchandise(doc):
	parent_list = []
	for d in doc.get('fabric_costing'):
		parent = frappe.db.get_value('Item Price', {'item_code':doc.name, 'price_list':d.merchandise_price_list},'name')
		if not parent:
			parent = make_item_price(doc.name, d.merchandise_price_list, d.rate)
		parent_list.append(parent.encode('ascii', 'ignore'))
		update_item_price_for_merchandise(parent, d)

def update_item_price_for_merchandise(parent,d):
	frappe.db.sql("update `tabItem Price` set price_list_rate='%s' where name='%s'"%(d.rate, parent))

# Commented code of services
"""
def update_price_list(args):
	data = args
	args = eval(args.costing_dict)
	parent_list = []
	for s in range(0, len(args)):
		parent = frappe.db.get_value('Item Price', {'item_code':data.get('parent'), 'price_list':args.get(str(s)).get('price_list')},'name')
		if not parent:
			parent = make_item_price(data.get('parent'), args.get(str(s)).get('price_list'))
		parent_list.append(parent.encode('ascii', 'ignore'))
		update_item_price(parent, data, args.get(str(s)).get('rate'))
	delete_non_present_entry(parent_list, data)
	return "Done"
"""

def make_item_price(item_code, price_list, rate=None):
	ip = frappe.new_doc('Item Price')
	ip.price_list = price_list
	ip.item_code = item_code
	ip.item_name = frappe.db.get_value('Item Name', item_code, 'item_name')
	ip.price_list_rate = rate or 1.00
	ip.currency = frappe.db.get_value('Price List', price_list, 'currency')  
	ip.save(ignore_permissions=True)
	return ip.name

def update_item_price(parent,data):
	frappe.errprint(parent)
	name = frappe.db.get_value('Customer Rate', {'parent':parent, 'branch': data.get('branch'), 'size': data.get('size')}, 'name')
	item_price_dict = get_dict(parent, data)
	if not name:
		name = frappe.get_doc(item_price_dict).insert()
	elif name:
		frappe.db.sql("update `tabCustomer Rate` set rate='%s' where name='%s'"%(data.service_rate, name))
	return True

def get_dict(parent, data):
	return {
				"doctype": "Customer Rate",
				"parent": parent,
				"branch": data.get('branch'),
				"parenttype": "Item Price",
				'parentfield': "customer_rate",
				"size":data.get('size'),
				"rate": data.service_rate,
			}

def delete_non_present_entry(parent, data):
	parent =  "','".join(parent)
	frappe.db.sql("delete from `tabCustomer Rate` where parent not in %s and branch='%s' and size='%s'"%("('"+parent+"')", data.branch, data.size))

def make_sales_bom(doc):
	if cint(doc.is_clubbed_product) == 1 and doc.is_stock_item == 'No':
		validate_sales_bom(doc)
		parent = frappe.db.get_value('Sales BOM', {'new_item_code': doc.name}, 'name')
		if not parent:
			sb = frappe.new_doc('Sales BOM')
			sb.new_item_code = doc.name
			for d in doc.get('sales_bom_item'):
				make_sales_bom_item(sb, d)
			sb.save(ignore_permissions = True)
		elif cint(doc.is_clubbed_product) == 1 and parent:
			update_sales_bom_item(parent, doc)
		delete_unnecessay_records(doc)

def make_sales_bom_item(obj, d):
	sbi= obj.append('sales_bom_items', {})
	sbi.item_code = d.item_code
	sbi.qty = d.qty
	return "Done"

def update_sales_bom_item(parent, doc):
	for d in doc.get('sales_bom_item'):
		name = frappe.db.get_value('Sales BOM Item', {'item_code': d.item_code, 'parent': parent, 'parenttype':'Sales BOM'}, 'name')
		if name:
			frappe.db.sql("update `tabSales BOM Item` set qty=%s where name='%s'"%(d.qty, name))
		else:
			obj = frappe.get_doc('Sales BOM', parent)
			make_sales_bom_item(obj, d)
			obj.save()

def validate_sales_bom(doc):
	if not doc.get('sales_bom_item'):
		frappe.throw('Mandatory Field: Sales Bom Item is mandatory')
	check_duplicate_item_code(doc)

def check_duplicate_item_code(doc):
	item_code_list = []
	for d in doc.get('sales_bom_item'):
		if frappe.db.get_value('Item', d.item_code, 'is_stock_item') != 'Yes':
			frappe.throw(_('Item Code "{0}"" at row {1} must be stock product').format(d.item_code, d.idx))
		if d.item_code in item_code_list:
			frappe.throw('Item Code can not be duplicate')
		item_code_list.append(d.item_code)

def delete_unnecessay_records(doc):
	sales_bom_item_list = []
	for s in doc.get('sales_bom_item'):
		sales_bom_item_list.append(frappe.db.get_value('Sales BOM Item', {'item_code':s.item_code, 'parent': s.parent, 'parenttype': 'Sales BOM'}, 'name'))
	bom_list =  "','".join(sales_bom_item_list)
	if bom_list:
		frappe.db.sql("""delete from `tabSales BOM Item` 
			where parenttype not in('Item') and name not in %s"""%("('"+bom_list+"')"))

def update_user_permissions_for_user(doc, method):
	assigen_user_permission(doc.branch, doc.email)

def update_user_permissions_for_emp(doc, method):
	assigen_user_permission(doc.branch, doc.user_id)

def assigen_user_permission(branch, email):
	if email and branch:
		branch_data, cost_center_data = get_user_details(email)
		if not branch_data:
			frappe.permissions.add_user_permission("Branch", branch, email)
		else:
			update_details(branch, branch_data)
		if not cost_center_data:
			frappe.permissions.add_user_permission("Cost Center", frappe.db.get_value('Branch', branch, 'cost_center'), email)
		else:
			update_details(frappe.db.get_value('Branch', branch, 'cost_center'), cost_center_data)			

def get_user_details(user_id):
	return frappe.db.get_value('DefaultValue',{'parent': user_id, 'defkey': 'Branch'}, 'name') , frappe.db.get_value('DefaultValue',{'parent': user_id, 'defkey': 'Cost Center'}, 'name')

def update_details(value, name):
	frappe.db.sql("""update `tabDefaultValue` set defvalue='%s' where name='%s'"""%(value, name))	

def make_barcode(doc, method):
	if not doc.barcode_image:
		barcode = generate_barcode(doc.name, doc.doctype)
		if barcode:
			image = '<img src="/files/%s/%s.svg">'%(doc.doctype, doc.name)
			make_barcode_log(doc.doctype, doc.name, image, doc.barcode_description)
	else:
		frappe.db.sql("update `tabBarcode Log` set barcode_description='%s' where doctype_name='%s' and barcode_id='%s'"%(doc.barcode_description, doc.doctype, doc.name))
		image = frappe.db.get_value('Barcode Log', {'doctype_name':doc.doctype, 'barcode_id': doc.name}, 'path')
	if image:
		description = ("""<div style="width:100%">{0}</div>""").format(doc.barcode_description or 'Barcode')
		doc.barcode_image = ("""<table><tr><td></td>{0}</tr><tr><td>{1}</td></tr></table>""").format(description, image)

def make_barcode_log(doctype_name, barcode_id, path, barcode_description):
	blog = frappe.new_doc('Barcode Log')			
	blog.doctype_name = doctype_name
	blog.barcode_id = barcode_id
	blog.path = path
	blog.barcode_description = barcode_description
	blog.save(ignore_permissions=True)
