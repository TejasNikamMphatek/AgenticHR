// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Challan Details", {
	refresh(frm) {

	},

    validate: function(frm) {
        var year = frm.doc.payroll_year;
        if (String(year).length !== 4) {
            frappe.msgprint(__('Payroll Year must be exactly 4 digits.'));
            frappe.validated = false;
        }
    }
});
