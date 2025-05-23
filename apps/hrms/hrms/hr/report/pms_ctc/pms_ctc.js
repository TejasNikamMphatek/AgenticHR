// Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["PMS CTC"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
	]
};
