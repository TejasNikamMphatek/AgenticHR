// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Generate FVU", {
	refresh(frm) {

	},
    upload_csi_file: function(frm) {
        const file_url = frm.doc.upload_csi_file;

        if (file_url) {
            const file_name = file_url.split('/').pop();
            const file_ext = file_name.split('.').pop().toLowerCase();

            if (file_ext !== 'csi') {
                frappe.msgprint(__('Only .csi files are allowed.'));
                frm.set_value('upload_csi_file', '');  // Clear the invalid file
            }
        }
    },
});
