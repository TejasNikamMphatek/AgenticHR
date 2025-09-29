frappe.listview_settings["Salary Structure"] = {
	refresh(frm) {
		$('.form-group[data-fieldname="is_active"] > div.dropdown').removeClass();
		$('.form-group[data-fieldname="is_active"] button.dropdown-toggle').remove();
		$('.form-group[data-fieldname="is_active"] > div').removeAttr('title data-original-title');
	},

	onload: function (list_view) {
		list_view.page.add_inner_button(__("Bulk Salary Structure Assignment"), function () {
			frappe.set_route("Form", "Bulk Salary Structure Assignment");
		});

		setTimeout(function () {
			$('.form-group[data-fieldname="is_active"] > div.dropdown').removeClass();
			$('.form-group[data-fieldname="is_active"] button.dropdown-toggle').remove();
			$('.form-group[data-fieldname="is_active"] > div').removeAttr('title data-original-title');
		}, 500);
	},
};
