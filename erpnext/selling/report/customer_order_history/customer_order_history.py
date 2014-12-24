# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	return columns, data

def get_columns():
	return [
			"Invoice No.:Link/Sales Invoice:80", "Customer Name:Link/Customer:150",
			"Product Name::120", "Booking Date:Date:80",  
			"Delivery Date:Date:80", "Trial Number::100", 
			"Trial Date:Date:100", "Current Status::120", "Amount Due::120",
			"Loyalty Points Redeemed::100", "Payment details::100", "Balance Amount::120"
		]