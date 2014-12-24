// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.views.calendar["Task"] = {
	field_map: {
		"start": "exp_start_date",
		"end": "exp_end_date",
		"id": "name",
		"title": __("subject"),
		"allDay": "allDay"
	},
	gantt: true,
	filters: [
		{
			"fieldtype": "Link", 
			"fieldname": "project", 
			"options": "Project", 
			"label": __("Project")
		}
	],
	get_events_method: "erpnext.projects.doctype.task.task.get_events"
}