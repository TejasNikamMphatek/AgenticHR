// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.query_reports["Holiday Calendar"] = {
	"filters": [
		{
			fieldname: "holiday_list",
			label: __("Holiday List"),
			fieldtype: "Link",
			options: "Holiday List",
		},
		// {
		// 	fieldname: "from_date",
		// 	label: __("From Date"),
		// 	fieldtype: "Date",
		// 	default: frappe.datetime.year_start()
		// },
		// {
		// 	fieldname: "to_date",
		// 	label: __("To Date"),
		// 	fieldtype: "Date",
		// 	default: frappe.datetime.year_end()
		// }
	],
	
	// onload: function(report) {
		
	// 	frappe.call({
	// 		method: "frappe.client.get_value",
	// 		args: {
	// 			doctype: "Employee",
	// 			filters: {
	// 				"user_id": frappe.session.user,
	// 				"status": "Active"
	// 			},
	// 			fieldname: ["holiday_list", "company"]
	// 		},
	// 		callback: function(r) {
	// 			if (r.message && r.message.holiday_list) {
	// 				report.set_filter_value("holiday_list", r.message.holiday_list);
	// 			} else if (r.message && r.message.company) {
	// 				// Fallback to company's default holiday list
	// 				frappe.call({
	// 					method: "frappe.client.get_value",
	// 					args: {
	// 						doctype: "Company",
	// 						filters: {"name": r.message.company},
	// 						fieldname: "default_holiday_list"
	// 					},
	// 					callback: function(company_r) {
	// 						if (company_r.message && company_r.message.default_holiday_list) {
	// 							report.set_filter_value("holiday_list", company_r.message.default_holiday_list);
	// 						}
	// 					}
	// 				});
	// 			}
	// 		}
	// 	});
	// }
};