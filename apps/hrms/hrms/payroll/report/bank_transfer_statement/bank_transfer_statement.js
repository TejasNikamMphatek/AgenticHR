// Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Bank Transfer Statement"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "start_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "end_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			label: __("Company"),
			fieldname: "company",
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		
		
		
	]
};
