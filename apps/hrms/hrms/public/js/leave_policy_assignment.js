frappe.ui.form.on('Leave Policy Assignment', {
    setup: function(frm) {
        frm.set_query("leave_policy", () => ({
            filters: { docstatus: 1 }
        }));

        frm.set_query("leave_period", () => ({
            filters: { is_active: 1 }
        }));
    },

    assignment_based_on: function(frm) {
        if (frm.doc.assignment_based_on === "Custom Range") {
            frm.set_value("leave_period", null);
            frm.set_df_property("effective_from", "reqd", 1);
            frm.set_df_property("effective_to", "reqd", 1);
            frm.set_df_property("leave_period", "reqd", 0);
            frm.set_value("effective_from", frappe.datetime.get_today());
            frm.set_value("effective_to", null);
        }

        else if (frm.doc.assignment_based_on === "Leave Period") {
            frm.set_df_property("leave_period", "reqd", 1);
            frm.set_df_property("effective_from", "reqd", 0);
            frm.set_df_property("effective_to", "reqd", 0);
            frm.set_value("effective_from", null);
            frm.set_value("effective_to", null);
        }

        else if (frm.doc.assignment_based_on === "Joining Date") {
            frm.set_df_property("leave_period", "reqd", 0);
            frm.set_df_property("effective_from", "reqd", 0);
            frm.set_df_property("effective_to", "reqd", 1);
            frm.set_value("leave_period", null);

            if (frm.doc.employee) {
                frappe.db.get_value("Employee", frm.doc.employee, "date_of_joining")
                    .then(r => {
                        if (r.message && r.message.date_of_joining) {
                            let doj = r.message.date_of_joining;
                            frm.set_value("effective_from", doj);

                            // 🔥 Fetch Active Leave Period
                            frappe.db.get_value("Leave Period", { "is_active": 1 }, ["from_date", "to_date"])
                                .then(lp => {
                                    if (lp.message && lp.message.to_date) {
                                        frm.set_value("effective_to", lp.message.to_date);
                                    } else {
                                        frappe.msgprint("No active Leave Period found.");
                                    }
                                });

                        } else {
                            frappe.msgprint({
                                title: __("Warning"),
                                message: __("No date of joining found for employee {0}.", [frm.doc.employee]),
                                indicator: "orange"
                            });
                            frm.set_value("effective_from", null);
                        }
                    });
            } else {
                frm.set_value("effective_from", null);
            }
        }

        frm.refresh_fields();
    },

    leave_period: function(frm) {
        if (frm.doc.assignment_based_on === "Leave Period" && frm.doc.leave_period) {
            frappe.db.get_value("Leave Period", frm.doc.leave_period, ["from_date", "to_date"], r => {
                frm.set_value("effective_from", r.from_date);
                frm.set_value("effective_to", r.to_date);
            });
        }
    },

    effective_from: function(frm) {
        if (frm.doc.employee && frm.doc.effective_from && frm.doc.leave_policy) {
            let end_date = frm.doc.effective_to || frm.doc.effective_from;
            check_overlap(frm, end_date);
        }
    },

    effective_to: function(frm) {
        if (frm.doc.employee && frm.doc.effective_from && frm.doc.effective_to && frm.doc.leave_policy) {
            check_overlap(frm, frm.doc.effective_to);
        }
    },

    leave_policy: function(frm) {
        if (frm.doc.employee && frm.doc.effective_from && frm.doc.leave_policy) {
            let end_date = frm.doc.effective_to || frm.doc.effective_from;
            check_overlap(frm, end_date);
        }
    },

    before_save: function(frm) {
        if (frm.doc.custom_override_existing_assignment) {
            frappe.call({
                method: "hrms.overrides.leave_policy_assignment.handle_leave_policy_override",
                args: {
                    employee: frm.doc.employee,
                    effective_from: frm.doc.effective_from,
                    effective_to: frm.doc.effective_to,
                    current_doc_name: frm.doc.name,
                    leave_policy: frm.doc.leave_policy
                },
                freeze: true,
                freeze_message: __("Overriding existing leave policy assignment..."),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __("Success"),
                            message: r.message.message,
                            indicator: "green"
                        });
                        frm.set_value('custom_override_existing_assignment', 0);
                    }
                }
            });
        }
    },

    validate: function(frm) {
        if (frm.doc.assignment_based_on === "Custom Range" && (!frm.doc.effective_from || !frm.doc.effective_to)) {
            frappe.throw(__("Effective From and Effective To dates are mandatory for Custom Range."));
        } else if (frm.doc.assignment_based_on === "Leave Period" && !frm.doc.leave_period) {
            frappe.throw(__("Leave Period is mandatory when Assignment Based On is Leave Period."));
        } else if (frm.doc.assignment_based_on === "Joining Date" && !frm.doc.effective_to) {
            frappe.throw(__("Effective To date is mandatory for Joining Date."));
        }
    }
});

function check_overlap(frm, end_date) {
    frappe.call({
        method: "hrms.overrides.leave_policy_assignment.get_overlapping_assignments",
        args: {
            employee: frm.doc.employee,
            effective_from: frm.doc.effective_from,
            effective_to: end_date,
            leave_policy: frm.doc.leave_policy,
            current_doc_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.assignments && r.message.assignments.length > 0) {
                let overlap = r.message.assignments[0];
                if (overlap.leave_policy === frm.doc.leave_policy) {
                    frappe.msgprint({
                        title: __("Error"),
                        message: __("Cannot override with the same leave policy ({0}) in the same period.").format(overlap.leave_policy),
                        indicator: "red"
                    });
                    frm.set_value('leave_policy', '');
                } else if (!frm.doc.custom_override_existing_assignment) {
                    frappe.confirm(
                        `Overlapping assignment detected: ${overlap.name} (${overlap.leave_policy}) from ${overlap.effective_from} to ${overlap.effective_to}. Do you want to override it?`,
                        () => frm.set_value('custom_override_existing_assignment', 1),
                        () => {
                            frm.set_value('leave_policy', '');
                            frm.set_value('effective_from', '');
                            frm.set_value('effective_to', '');
                        }
                    );
                }
            }
        }
    });
}
