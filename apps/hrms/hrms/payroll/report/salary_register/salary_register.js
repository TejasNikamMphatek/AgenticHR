frappe.query_reports["Salary Register"] = {
	onload: function (report) {
		if (frappe.user.has_role("Projects Manager") && !frappe.user.has_role("HR Manager")) {
			const employee_filter = report.get_filter("employee");

			// Limit employee dropdown to only the logged-in PM's employee record
			employee_filter.df.get_query = function () {
				return {
					query: "erpnext.setup.doctype.employee.employee.get_employee_for_self_only",
				};
			};

			// Optional: make it read-only & auto-fill
			frappe.call({
				method: "erpnext.setup.doctype.employee.employee.get_logged_in_employee",
				callback: function (r) {
					if (r.message) {
						report.set_filter_value("employee", r.message);
						employee_filter.df.read_only = 1;
						employee_filter.refresh();
					}
				},
			});
		}
	},

	filters: [
		{
			fieldname: "from_date",
			label: __("From"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "100px",
		},
		{
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "100px",
		},
		{
			fieldname: "currency",
			fieldtype: "Link",
			options: "Currency",
			label: __("Currency"),
			default: erpnext.get_currency(frappe.defaults.get_default("Company")),
			width: "50px",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			width: "100px",
		},
		{
			fieldname: "docstatus",
			label: __("Document Status"),
			fieldtype: "Select",
			options: ["Draft", "Submitted", "Cancelled"],
			default: "Submitted",
			width: "100px",
			read_only: 1,
		},
	],
};
