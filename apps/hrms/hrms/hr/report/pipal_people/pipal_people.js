frappe.query_reports["Pipal People"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee Number"),
			fieldtype: "Data",
			
		},
		{
			fieldname: "employee_name",
			label: __("Employee Name"),
			fieldtype: "Data",
			
		},
	],
	// onload: function(report) {
	// 	$('.menu-btn-group').addClass('hide d-none');
    // },
};
