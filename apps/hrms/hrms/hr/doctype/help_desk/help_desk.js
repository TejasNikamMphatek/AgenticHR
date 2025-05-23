// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Help Desk", {
// 	refresh(frm) {

// 	},
// });


frappe.listview_settings["Help Desk"] = {
	add_fields: ["help_status"],
	filters: [["help_status", "!=", "Completed"]],
	get_indicator: function (doc) {
		return [
			__(doc.help_status),
			frappe.utils.guess_colour(doc.help_status),
			"help_status,=," + doc.help_status,
		];
	},
};