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
			"Cust ID.:Link/Customer:80", "Full Name::150",
			"Customer Category::110", "Mobile::120",
			"Address::80",  
			"Total Loyalty Points:Date:80", "Redeemed Points::100", 
			"Balance Redeemable Points:Date:100", "Any Unpaid Amount::80"
		]