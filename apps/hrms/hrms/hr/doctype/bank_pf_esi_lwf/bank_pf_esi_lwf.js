frappe.ui.form.on("Bank PF ESI LWF", {
    validate(frm) {
        // Regex for numeric only
        const numeric = /^[0-9]*$/;

        if (frm.doc.uan && !numeric.test(frm.doc.uan)) {
            frappe.throw("UAN must contain numeric values only.");
        }

        if (frm.doc.esi_number && !numeric.test(frm.doc.esi_number)) {
            frappe.throw("ESI Number must contain numeric values only.");
        }
    }
});
