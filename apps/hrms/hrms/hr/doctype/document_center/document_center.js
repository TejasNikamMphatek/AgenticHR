frappe.ui.form.on("Document Center", {
    refresh(frm) {
        $('#navbar-breadcrumbs li:last').hide();

        // Verify Digital Signature Button
        if (frm.doc.document && frm.doc.verification_status !== "Verified") {
            frm.add_custom_button(__('Verify Digital Signature'), function() {
                frappe.call({
                    method: "hrms.hr.doctype.document_center.document_center.verify_digital_signature",
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        if (r.message && r.message.status === "success") {
                            frappe.msgprint(r.message.message);
                            frm.reload_doc();
                        } else {
                            frappe.msgprint("Verification failed or invalid signature.");
                        }
                    },
                    error: function(err) {
                        frappe.msgprint("Verification failed.");
                        console.error(err);
                    }
                });
            });
        }

        // Download Button (only if verified)
        if (frm.doc.verification_status === "Verified") {
            frm.add_custom_button(__('Download Verified Form 16'), function() {
                window.location.href = `/api/method/hrms.hr.doctype.document_center.document_center.force_download?docname=${frm.doc.name}`;
            });
        }
    },
});
