// Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["ESI Deduction Report"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
	]
};

// frappe.require("hrms/hrms/public/js/salary_slip_deductions_report_filters.js", function () {
// 	frappe.query_reports["ESI Deduction Report"] =
// 		hrms.salary_slip_deductions_report_filters;

// 		console.log(hrms.salary_slip_deductions_report_filters,"-----------")
// });
