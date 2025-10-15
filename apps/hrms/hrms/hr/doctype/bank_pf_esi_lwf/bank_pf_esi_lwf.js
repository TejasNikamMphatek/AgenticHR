frappe.ui.form.on("Bank PF ESI LWF", {
    validate(frm) {
        // ✅ UAN Validation
        if (frm.doc.uan && !/^\d{12}$/.test(frm.doc.uan)) {
            frappe.throw(__("PF UAN must be exactly 12 digits and contain only numbers."));
        }

        // ✅ Bank Account Number (fetched one)
        if (frm.doc.bank_account_number && !/^\d+$/.test(frm.doc.bank_account_number)) {
            frappe.throw(__("Bank Account Number must contain only numbers."));
        }

        // ✅ Bank Account No. (manual one)
        if (frm.doc.bank_account_no && !/^\d+$/.test(frm.doc.bank_account_no)) {
            frappe.throw(__("Bank Account No. must contain only numbers."));
        }
    }
});
