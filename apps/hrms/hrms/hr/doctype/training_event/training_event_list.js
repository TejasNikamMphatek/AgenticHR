frappe.listview_settings["Training Event"] = {
	refresh(frm) {
		$('div[data-fieldname="event_status"]> div.dropdown').removeClass();
		$('div[data-fieldname="event_status"] button.dropdown-toggle').remove();
		$('.form-group[data-fieldname="event_status"] > div').removeAttr('title data-original-title');

	},

	onload: function (list_view) {

		setTimeout(function () {
			$('div[data-fieldname="event_status"]> div.dropdown').removeClass();
			$('div[data-fieldname="event_status"] button.dropdown-toggle').remove();
			$('.form-group[data-fieldname="event_status"] > div').removeAttr('title data-original-title');

		}, 500);
	},
};