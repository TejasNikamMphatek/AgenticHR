// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Form 24Q Settings", {
	refresh(frm) {

	},

    validate: function(frm) {
        is_hr_manager = frappe.user.has_role(['HR Manager'])
        if (!is_hr_manager) {
            frappe.msgprint(__('Only HR Manager or Admin can save changes'), 'Permission Not Valid');
            frappe.validated = false;
        }
    }
});
