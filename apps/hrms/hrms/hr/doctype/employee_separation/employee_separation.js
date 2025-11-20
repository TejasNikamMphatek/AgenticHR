// Copyright (c) 2018,
// mPHATEK Systems Pvt. Ltd.
// For license information, please see license.txt

frappe.ui.form.on("Employee Separation", {

    onload(frm) {
        // Lock PM/HR reviewed fields for Employees
        if (frappe.user.has_role("Employee")) {
            ["pm_reviewed", "hr_reviewed"].forEach(fieldname => {
                if (frm.fields_dict[fieldname]) {
                    frm.set_df_property(fieldname, "read_only", 1);
                    frm.fields_dict[fieldname].$input?.prop("disabled", true);
                    frm.fields_dict[fieldname].$wrapper
                        .find("input[type='checkbox']")
                        .css({ "pointer-events": "none", opacity: 0.6 });
                }
            });
        }
    },

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

        // ========== CASE 1: NEW DOCUMENT ==========
        if (frm.is_new()) {
            employee_editable_fields.forEach(field => {
                frm.set_df_property(field, "read_only", 0);
            });

            // Lock PM/HR review fields
            if (frappe.user.has_role("Employee")) {
                ["pm_reviewed", "hr_reviewed"].forEach(fieldname => {
                    if (frm.fields_dict[fieldname]) {
                        frm.set_df_property(fieldname, "read_only", 1);
                        frm.fields_dict[fieldname].$input?.prop("disabled", true);
                    }
                });
            }

            frm.enable_save();
            return;
        }

        // ========== CASE 2: EXISTING DOCUMENT ==========
        Object.keys(frm.fields_dict).forEach(fieldname => {
            frm.set_df_property(fieldname, "read_only", 1);
        });
        frm.disable_save();

        // ========== CASE 2A: PM Can Edit ==========
        if (is_manager) {
            manager_editable_fields.forEach(field => {
                frm.set_df_property(field, "read_only", 0);
            });
            frm.enable_save();
        }

        // ========== CASE 2B: Employee Cannot Edit ==========
        else if (is_creator && !is_manager) {
            frm.disable_save();
        }

        // ========== CASE 3: View Employee Button ==========
        if (frappe.user.has_role(["HR Manager", "Projects Manager"]) && frm.doc.employee) {
            frm.add_custom_button(
                __("Employee"),
                () => frappe.set_route("Form", "Employee", frm.doc.employee),
                __("View")
            );
        }

        // ========== WORKFLOW: Hide Submit for non-HR ==========
        if (
            frm.doc.docstatus === 0 &&
            !frappe.user.has_role("HR Manager") &&
            !frappe.user.has_role("System Manager")
        ) {
            $(".btn-submit").hide();
        }

        // ========== HR/SysMgr Submit Button ==========
        if (
            frm.doc.docstatus === 0 &&
            (frappe.user.has_role("HR Manager") || frappe.user.has_role("System Manager")) &&
            frm.doc.hr_reviewed === 1
        ) {
            frm.page.set_primary_action(
                __("Submit"),
                function () {
                    if (frm.is_dirty()) {
                        frm.save().then(() => frm.save("Submit"));
                    } else {
                        frm.save("Submit");
                    }
                },
                "btn-primary"
            );
        }

        // ========== PM → HR Forward Logic (FULL GITHUB VERSION) ==========
        if (
            frappe.user.has_role("Projects Manager") &&
            frm.doc.docstatus === 0 &&
            !frm.doc.__islocal &&
            frm.doc.pm_reviewed === 1 &&
            frm.doc.hr_reviewed === 0
        ) {
            frm.page.add_inner_button(__("Forward to HR"), function () {
                frappe.confirm(
                    __("Are you sure you want to forward this resignation to HR for review?"),
                    () => {
                        frappe.model.set_value(frm.doctype, frm.doc.name, "hr_reviewed", 1);
                        frm.save()
                            .then(() => {
                                frappe.show_alert({
                                    message: __("Successfully forwarded to HR for approval."),
                                    indicator: "green"
                                });
                                frappe.msgprint({
                                    title: __("Forwarded Successfully"),
                                    message: __(
                                        "This resignation has been forwarded to the HR Manager for review. HR will now take further action."
                                    ),
                                    indicator: "green"
                                });
                                frm.reload_doc();
                            })
                            .catch(() => {
                                frappe.msgprint({
                                    title: __("Error"),
                                    message: __("Something went wrong while forwarding to HR."),
                                    indicator: "red"
                                });
                            });
                    }
                );
            });
        }

        // ========== HR Reminder ==========
        if (
            frappe.user.has_role("HR Manager") &&
            frm.doc.docstatus === 0 &&
            frm.doc.hr_reviewed === 0
        ) {
            frappe.msgprint(
                __("⏳ Waiting for PM to forward using 'Forward to HR' button.")
            );
        }
    },

    // Auto-set pm_reviewed on employee's first save
    before_save(frm) {
        if (
            frappe.user.has_role("Employee") &&
            frm.doc.pm_reviewed === 0 &&
            !frm.doc.__islocal
        ) {
            frappe.model.set_value(frm.doctype, frm.doc.name, "pm_reviewed", 1);
        }
    }
});
