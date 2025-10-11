// Copyright (c) 2024, mPHATEK Systems Pvt. Ltd.
// For license information, please see license.txt

frappe.ui.form.on("Help Desk", {
    refresh(frm) {
        const employee_editable_fields = [
            "employee", 
            "employee_name", 
            "employee_email", 
            "subject", 
            "category",
            "default_email_to",
            "cc",
            "priority",
            "discription",
            "attachment",
			"application_date"
        ];

        const hr_editable_fields = ["priority", "help_status"];

        const is_creator = frm.doc.owner === frappe.session.user;
        const is_hr = frappe.user.has_role("HR Manager");

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
        // Make all fields read-only first
        Object.keys(frm.fields_dict).forEach(fieldname => {
            frm.set_df_property(fieldname, "read_only", 1);
        });
        frm.disable_save();

        // -----------------------
        // CASE 2A: HR Manager can edit "priority" and "help_status"
        // -----------------------
        if (is_hr) {
            hr_editable_fields.forEach(field => {
                if (frm.fields_dict[field]) {
                    frm.set_df_property(field, "read_only", 0);
                }
            });
            frm.enable_save();
        }

        // -----------------------
        // CASE 2B: Employee (Creator) cannot edit after save
        // -----------------------
        else if (is_creator && !is_hr) {
            frm.disable_save();
        }

        // -----------------------
        // CASE 3: Add "View Employee" Button for HR Manager
        // -----------------------
        if (is_hr && frm.doc.employee) {
            frm.add_custom_button(
                __("Employee"),
                () => frappe.set_route("Form", "Employee", frm.doc.employee),
                __("View")
            );
        }
    }
});
