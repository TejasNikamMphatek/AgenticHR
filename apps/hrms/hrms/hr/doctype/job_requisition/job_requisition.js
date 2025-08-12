// Complete JavaScript Fix (job_requisition.js)
frappe.ui.form.on("Job Requisition", {
    refresh: function (frm) {
        // Fix any invalid time_to_fill values on the client side
        if (frm.doc.time_to_fill && (frm.doc.time_to_fill === 0 || frm.doc.time_to_fill === "0" || frm.doc.time_to_fill === "")) {
            frm.doc.time_to_fill = null;
        }

        // Check if the form is not new and status is not Filled, On Hold, or Cancelled
        if (!frm.doc.__islocal && !["Filled", "On Hold", "Cancelled"].includes(frm.doc.status)) {
            // Ensure designation is defined and not empty
            if (frm.doc.designation && frm.doc.designation.trim()) {
                frappe.call({
                    method: "hrms.hr.doctype.job_requisition.job_requisition.get_pending_referral_count",
                    args: {
                        designation: frm.doc.designation,
                    },
                    callback: function (r) {
                        if (r.message !== undefined) {
                            const count = r.message || 0;
                            if (count > 0) {
                                const link_text = count > 1 ? __("Employee Referrals") : __("Employee Referral");
                                const link_html = `<a id="referral_links" style="text-decoration: underline;">${link_text}</a>`;
                                const headline = __("{} {} open for this position.", [count, link_html]);

                                frm.dashboard.clear_headline();
                                frm.dashboard.set_headline(headline, "yellow");

                                // Use frappe.after_ajax for better DOM handling
                                frappe.after_ajax(() => {
                                    $("#referral_links").off("click").on("click", function (e) {
                                        e.preventDefault();
                                        frappe.set_route("List", "Employee Referral", {
                                            for_designation: frm.doc.designation,
                                            status: "Pending",
                                        });
                                    });
                                });
                            }
                        }
                    },
                    error: function (r) {
                        console.error("Error fetching pending referral count:", r);
                        frappe.msgprint({
                            title: __("Error"),
                            message: __("Failed to fetch pending referral count. Please try refreshing the page."),
                            indicator: "red",
                        });
                    }
                });
            }
        }

        // Add action buttons if status is "Open & Approved"
        if (frm.doc.status === "Open & Approved") {
            frm.add_custom_button(
                __("Create Job Opening"),
                () => {
                    frappe.model.open_mapped_doc({
                        method: "hrms.hr.doctype.job_requisition.job_requisition.make_job_opening",
                        frm: frm,
                    });
                },
                __("Actions")
            );

            frm.add_custom_button(
                __("Associate Job Opening"),
                () => {
                    frappe.prompt(
                        {
                            label: __("Job Opening"),
                            fieldname: "job_opening",
                            fieldtype: "Link",
                            options: "Job Opening",
                            reqd: 1,
                            get_query: () => {
                                const filters = {
                                    company: frm.doc.company,
                                    status: "Open",
                                    designation: frm.doc.designation,
                                };

                                if (frm.doc.department) {
                                    filters.department = frm.doc.department;
                                }

                                return { filters: filters };
                            },
                        },
                        (values) => {
                            frm.call("associate_job_opening", {
                                job_opening: values.job_opening,
                            });
                        },
                        __("Associate Job Opening"),
                        __("Submit")
                    );
                },
                __("Actions")
            );

            frm.page.set_inner_btn_group_as_primary(__("Actions"));
        }
    },

    // Handle time_to_fill field display issues
    onload: function(frm) {
        // Override the time_to_fill field formatter to handle invalid values
        if (frm.fields_dict.time_to_fill) {
            frm.fields_dict.time_to_fill.formatter = function(value, df, options, doc) {
                if (!value || value === 0 || value === "0") {
                    return "-";
                }
                return frappe.format(value, df, options, doc);
            };
        }
    },

    // Validate before save
    validate: function(frm) {
        // Clean up time_to_fill if it's invalid
        if (frm.doc.time_to_fill && (frm.doc.time_to_fill === 0 || frm.doc.time_to_fill === "0")) {
            frm.doc.time_to_fill = null;
        }
    }
});

// Global fix for duration formatting issues
frappe.form.formatters.Duration = function(value, df, options) {
    if (!value || value === 0 || value === "0") {
        return "-";
    }
    
    // Use frappe's built-in duration formatter
    return frappe.format_duration(value);
};