// Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Form-16-Upload", {
	refresh: function(frm) {
        // Show Part A files
        frm.add_custom_button(__('Show Part A Files'), function() {
            frappe.call({
                method: "hrms.hr.doctype.form_16_upload.form_16_upload.get_extracted_file_list",
                args: { docname: frm.doc.name, part_name: "PartA" },
                callback: function(r) {
                    if (r.message && r.message.length) {
                        frappe.msgprint("Part A Files:<br>" + r.message.join("<br>"));
                        console.log("Part A Files:", r.message);
                    } else {
                        frappe.msgprint("No Part A files found.");
                    }
                }
            });
        });

        // Show Part B files
        frm.add_custom_button(__('Show Part B Files'), function() {
            frappe.call({
                method: "hrms.hr.doctype.form_16_upload.form_16_upload.get_extracted_file_list",
                args: { docname: frm.doc.name, part_name: "PartB" },
                callback: function(r) {
                    if (r.message && r.message.length) {
                        frappe.msgprint("Part B Files:<br>" + r.message.join("<br>"));
                        console.log("Part B Files:", r.message);
                    } else {
                        frappe.msgprint("No Part B files found.");
                    }
                }
            });
        });
    },

    extract_part_a: function(frm) {
        frappe.call({
            method: "hrms.hr.doctype.form_16_upload.form_16_upload.extract_part_a",
            args: { docname: frm.doc.name },
            callback: function(r) {
                frappe.msgprint(r.message);
            }
        });
    },
    extract_part_b: function(frm) {
        frappe.call({
            method: "hrms.hr.doctype.form_16_upload.form_16_upload.extract_part_b",
            args: { docname: frm.doc.name },
            callback: function(r) {
                frappe.msgprint(r.message);
            }
        });
    },

    apply_digital_signature_part_a: function(frm) {
        frappe.call({
            method: "hrms.hr.doctype.form_16_upload.form_16_upload.apply_digital_signature_part_a",
            args: { docname: frm.doc.name },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint("✅ Digital signatures applied successfully.");
                } else {
                    frappe.msgprint("Failed to apply digital signatures.");
                }
            },
            error: function(r) {
                console.error(r)
                frappe.msgprint("applying digital signatures - Failed");
            }
        });
    },

    apply_digital_signature_part_b: function(frm) {
        frappe.call({
            method: "hrms.hr.doctype.form_16_upload.form_16_upload.apply_digital_signature_part_b",
            args: { docname: frm.doc.name },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint("✅ Digital signatures applied successfully.");
                } else {
                    frappe.msgprint("Failed to apply digital signatures.");
                }
            },
            error: function(r) {
                console.error(r)
                frappe.msgprint("applying digital signatures - Failed");
            }
        });
    },

    publish_part_a:function(frm){
        frappe.call({
            method: "hrms.hr.doctype.form_16_upload.form_16_upload.publish_part_a",
            args: { docname: frm.doc.name, part_name: "PartA" },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(r.message.status);
                    // console.log("Part A Files:", r);
                } else {
                    frappe.msgprint("No Part A files found.");
                }
            }
        });
    },

    publish_part_b:function(frm){
        frappe.call({
            method: "hrms.hr.doctype.form_16_upload.form_16_upload.publish_part_b",
            args: { docname: frm.doc.name, part_name: "PartB" },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(r.message.status);
                    // console.log("Part B Files:", r);
                } else {
                    frappe.msgprint("No Part A files found.");
                }
            }
        });
    }



});
