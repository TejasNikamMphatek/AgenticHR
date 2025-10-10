// Copyright (c) 2018, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on("Employee Separation", {
    refresh(frm) {
        const employee_editable_fields = [
            "employee", 
            "required_lwd", 
            "reason", 
            "alternate_email_id", 
            "alternate_mobile_number",
            "exit_reason_for_employee"
        ];

        const manager_editable_fields = [
            "resign_status", 
            "approved_lwd",
			"exit_reason_for_employee",
			"final_decision_status"
        ];

        const is_creator = frm.doc.owner === frappe.session.user;
        const is_manager = frappe.user.has_role("Projects Manager");

        // -----------------------
        // CASE 1: NEW DOCUMENT (Employee creating new application)
        // -----------------------
        if (frm.is_new()) {
            employee_editable_fields.forEach(field => {
                frm.set_df_property(field, "read_only", 0);
            });
            frm.enable_save();
            return;
        }

        // -----------------------
        // CASE 2: AFTER SAVE (Existing Document)
        // -----------------------

        // Default: make everything read-only
        Object.keys(frm.fields_dict).forEach(fieldname => {
            frm.set_df_property(fieldname, "read_only", 1);
        });
        frm.disable_save();

        // -----------------------
        // CASE 2A: Projects Manager
        // -----------------------
        if (is_manager) {
            manager_editable_fields.forEach(field => {
                frm.set_df_property(field, "read_only", 0);
            });
            frm.enable_save();
        }

        // -----------------------
        // CASE 2B: Employee (Creator)
        // -----------------------
        else if (is_creator && !is_manager) {
            // Employee should NOT be able to edit anything after save
            frm.disable_save();
        }

        // -----------------------
        // CASE 3: Add "View Employee" Button for HR or Manager
        // -----------------------
        if (frappe.user.has_role(['HR Manager', 'Projects Manager']) && frm.doc.employee) {
            frm.add_custom_button(
                __("Employee"),
                () => frappe.set_route("Form", "Employee", frm.doc.employee),
                __("View")
            );
        }
    }
});

