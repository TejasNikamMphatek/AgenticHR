frappe.query_reports["Income Tax Deductions"] = {
	filters: [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			reqd: 0,
			hidden: 1, // Hidden by default, will be shown conditionally
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			reqd: 1,
			options: [
				{ value: 1, label: __("Jan") },
				{ value: 2, label: __("Feb") },
				{ value: 3, label: __("Mar") },
				{ value: 4, label: __("Apr") },
				{ value: 5, label: __("May") },
				{ value: 6, label: __("June") },
				{ value: 7, label: __("July") },
				{ value: 8, label: __("Aug") },
				{ value: 9, label: __("Sep") },
				{ value: 10, label: __("Oct") },
				{ value: 11, label: __("Nov") },
				{ value: 12, label: __("Dec") },
			]
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Select",
			options: [],
			reqd: 1,
		},
	],
	
	onload: function () {
		// Get years for the year filter
		frappe.call({
			method: "hrms.payroll.report.provident_fund_deductions.provident_fund_deductions.get_years",
			callback: function (r) {
				var year_filter = frappe.query_report.get_filter("year");
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			},
		});

		// Check user permissions and setup employee filter accordingly
		frappe.call({
			method: "hrms.payroll.report.income_tax_deductions.income_tax_deductions.setup_employee_filter",
			callback: function (r) {
				if (r.message) {
					var employee_filter = frappe.query_report.get_filter("employee");
					
					if (r.message.is_system_manager) {
						// System Manager can see all employees
						employee_filter.df.hidden = 0;
						employee_filter.df.reqd = 0;
					} else if (r.message.employee_id) {
						// Regular employee - set their employee ID automatically
						employee_filter.df.hidden = 1;
						employee_filter.df.default = r.message.employee_id;
						employee_filter.set_input(r.message.employee_id);
					}
					
					employee_filter.refresh();
				}
			},
		});
	},
};