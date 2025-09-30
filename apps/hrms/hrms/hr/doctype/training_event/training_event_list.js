frappe.listview_settings["Training Event"] = {
	refresh(frm) {
		$('div[data-fieldname="event_status"].dropdown').removeClass();
		$('div[data-fieldname="event_status"] button.dropdown-toggle').remove();

	},

	onload: function (list_view) {
	

		setTimeout(function () {
			$('div[data-fieldname="event_status"].dropdown').removeClass();
			$('div[data-fieldname="event_status"] button.dropdown-toggle').remove();

		}, 500);
	},
};