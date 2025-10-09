// Copyright (c) 2018, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Separation", {
	refresh(frm) {
		const editable_fields = ["employee","required_lwd", "reason", "alternate_email_id", "alternate_mobile_number"];
		const is_creator = frm.doc.owner === frappe.session.user;

		editable_fields.forEach(field => {
			frm.set_df_property(field, "read_only", frm.is_new() ? 0 : is_creator ? 0 : 1);
		});

		if (frappe.user.has_role(['HR Manager', 'Projects Manager']) && frm.doc.employee) {
			frm.add_custom_button(
				__("Employee"),
				() => frappe.set_route("Form", "Employee", frm.doc.employee),
				__("View")
			);
		}
	}
});
