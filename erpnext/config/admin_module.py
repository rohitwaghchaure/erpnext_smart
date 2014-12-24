from frappe import _

def get_data():
	return [
		{
			"label": _("Documents"),
			"icon": "icon-star",
			"items": [
				{
					"type": "page",
					"name": "admin-charts",
					"icon": "icon-sitemap",
					"label": _("Dashboard"),
					"link": "admin-charts",
					"description": _("Dashboard"),
				},
				{
					"type": "doctype",
					"label":"Authentication Approval",
					"name": "Admin Signature",
					"description": _("Admin Signature"),
				},
				{
					"type": "doctype",
					"name": "Pricing Rule",
					"label": _("Offer"),
					"description": _("List of offer"),
				},
				{
					"type":"page",
					"name":"report-template",
					"icon": "icon-sitemap",
					"label": _("External Product Catalog"),
					"link": "report-template",
					"description": _("External Product Catalog"),
				}
			]
		},
		
		{
			"label": _("Master"),
			"icon": "icon-cog",
			"items": [
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer Details"),
				},
				{
					"type": "doctype",
					"name": "Supplier",
					"description": _("Supplier Details"),
				},
				{
					"type": "doctype",
					"name": "Measurement Template",
					"description": _("Collection of Measurement Fields"),
				},
				{
					"type": "doctype",
					"name": "Measurement Formula",
					"description": _("Measurement Formula"),
				},
				{
					"type": "doctype",
					"name": "Item",
					"description": _("All types of Product like Tailoring, Merchandise etc."),
				},
			]
		},
		{
			"label": _("Setup"),
			"icon": "icon-cog",
			"items": [
				{
					"type": "doctype",
					"name": "Company",
					"description": _("Company Details"),
				},
				{
					"type": "doctype",
					"name": "Branch",
					"description": _("Branch Details"),
				},
				{
					"type": "doctype",
					"name": "Service",
					"description": _("List of Services"),
				},
				{
					"type": "doctype",
					"name": "Measurement",
					"label" : _("Measurement Fields"),
					"description": _("List of Measurement"),
				},
				{
					"type": "doctype",
					"name": "Style",
					"description": _("Style"),
				},
				{
					"type": "doctype",
					"name": "Process",
					"description": _("List of Process"),
				},
				{
					"type": "doctype",
					"name": "Size",
					"description": _("Size"),
				},
				{
					"type": "doctype",
					"name": "Width",
					"description": _("Width"),
				},
			]
		},
		{
			"label": _("Main Reports"),
			"icon": "icon-table",
			"items": [
				{
					"type": "page",
					"name": "purchase-analytics",
					"label": _("Purchase Analytics"),
					"icon": "icon-bar-chart",
				},
			]
		},
		{
			"label": _("Standard Reports"),
			"icon": "icon-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Items To Be Requested",
					"doctype": "Item"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Requested Items To Be Ordered",
					"doctype": "Material Request"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Material Requests for which Supplier Quotations are not created",
					"doctype": "Material Request"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Item-wise Purchase History",
					"doctype": "Item"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Item-wise Last Purchase Rate",
					"doctype": "Item"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Purchase Order Trends",
					"doctype": "Purchase Order"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Supplier Addresses and Contacts",
					"doctype": "Supplier"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Supplier-Wise Sales Analytics",
					"doctype": "Stock Ledger Entry"
				}
			]
		},
	]
