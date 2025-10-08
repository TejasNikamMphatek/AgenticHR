frappe.listview_settings["Employee"] = {
	onload: function (listview) {
		$('.btn[data-label="Add Employee"] span.hidden-xs').html('Start Employee Onboarding');
	},
	refresh(frm) {
		$('.btn[data-label="Add Employee"] span.hidden-xs').html('Start Employee Onboarding');
		$('.btn.btn-default.btn-new-doc.hidden-xs').text('Start Employee Onboarding');

	},

	add_fields: ["status", "branch", "department", "designation", "image"],
	filters: [["status", "=", "Active"]],
	get_indicator: function (doc) {
		var indicator = [__(doc.status), frappe.utils.guess_colour(doc.status), "status,=," + doc.status];
		indicator[1] = { Active: "green", Inactive: "red", Left: "gray", Suspended: "orange" }[doc.status];
		return indicator;
	},
};
