// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Document Center", {
    refresh(frm) {
        $('#navbar-breadcrumbs li:last').hide();
    },

    download_document: function(frm) {
        // Directly call the API method as a GET request
        window.location.href = `/api/method/hrms.hr.doctype.document_center.document_center.force_download?docname=${frm.doc.name}`;
    }

});
