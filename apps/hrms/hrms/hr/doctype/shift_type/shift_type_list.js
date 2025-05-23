frappe.listview_settings["Shift Type"] = {
	
		onload: function (list_view) {
			if(frappe.user.has_role("HR Manager")){
				list_view.page.add_inner_button(__("Shift Assignment Tool"), function () {
					frappe.set_route("Form", "Shift Assignment Tool");
				});
			}
		},
	
};
