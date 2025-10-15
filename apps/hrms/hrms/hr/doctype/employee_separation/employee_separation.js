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

        // Workflow Conditions for Employee ==> PM ==> HR 
        
        // Hide native Submit for non-HR/System Manager
        if (frm.doc.docstatus === 0 && !frappe.user.has_role('HR Manager') && !frappe.user.has_role('System Manager')) {
            $('.btn-submit').hide();
        }

        // Submit button for HR/System Manager (visible only after PM forward)
        if (frm.doc.docstatus === 0 && (frappe.user.has_role('HR Manager') || frappe.user.has_role('System Manager')) && frm.doc.hr_reviewed === 1) {
            frm.page.set_primary_action(__('Submit'), function() {
                if (frm.is_dirty()) {
                    frm.save().then(() => {
                        frm.save('Submit');  // Native submit
                    });
                } else {
                    frm.save('Submit');
                }
            }, 'btn-primary');
        }

        // PM: "Forward to HR" button (visible only after employee forward, set flag on click only)
        if (frappe.user.has_role('Projects Manager') && frm.doc.docstatus === 0 && !frm.doc.__islocal && frm.doc.pm_reviewed === 1 && frm.doc.hr_reviewed === 0) {
            frm.page.add_inner_button(__('Forward to HR'), function() {
                frappe.model.set_value(frm.doctype, frm.doc.name, 'hr_reviewed', 1);
                frm.save();
                frappe.msgprint('Forwarded to HR for approval.');
            });
        }

        // Warnings
        // if (frappe.user.has_role('Projects Manager') && frm.doc.docstatus === 0 && frm.doc.pm_reviewed === 0) {
        //     frappe.msgprint('Waiting for Employee to forward ("Send to PM" button).');
        // }
        if (frappe.user.has_role('HR Manager') && frm.doc.docstatus === 0 && frm.doc.hr_reviewed === 0) {
            frappe.msgprint('Waiting for PM to forward ("Forward to HR" button).');
        }

        // Auto-forward to PM after Employee's first save (set pm_reviewed = 1)
        frappe.ui.form.on('Employee Separation', {
            before_save: function(frm) {
                if (frappe.user.has_role('Employee') && frm.doc.pm_reviewed === 0 && !frm.doc.__islocal) {
                    frappe.model.set_value(frm.doctype, frm.doc.name, 'pm_reviewed', 1);
                }
            }
        });
    }
});