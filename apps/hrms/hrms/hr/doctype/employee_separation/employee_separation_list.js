frappe.listview_settings["Employee Separation"] = {
	add_fields: ["resign_status", "employee_name", "department"],
	filters: [["resign_status", "=", "Pending"]],
	get_indicator: function (doc) {
		return [
			__(doc.resign_status),
			frappe.utils.guess_colour(doc.resign_status),
			"resign_status,=," + doc.resign_status,
		];
	},
};
