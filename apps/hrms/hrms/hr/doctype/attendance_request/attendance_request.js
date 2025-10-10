// Copyright (c) 2018, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on("Attendance Request", {
	refresh(frm) {

		const editable_fields = ["employee","from_date", "to_date", "half_day", "half_day_date", "reason", "explanation"];
		const is_creator = frm.doc.owner === frappe.session.user;

		editable_fields.forEach(field => {
			frm.set_df_property(field, "read_only", frm.is_new() ? 0 : is_creator ? 0 : 1);
		});


        
        if (frm.is_new()) {
            editable_fields.forEach(field => {
                frm.set_df_property(field, "read_only", 0);
            });
            frm.enable_save();
            return;
        }
        
        if (!frm.is_new()) {

            if (is_creator && !frappe.user.has_role("Leave Approver")) {
               
                Object.keys(frm.fields_dict).forEach(fieldname => {
                    frm.set_df_property(fieldname, "read_only", 1);
                });
                frm.disable_save();
            }

            
            else if (frappe.user.has_role("Leave Approver")) {
                
                Object.keys(frm.fields_dict).forEach(fieldname => {
                    frm.set_df_property(fieldname, "read_only", 1);
                });

                
                approver_editable_fields.forEach(field => {
                    frm.set_df_property(field, "read_only", 0);
                });

                
                frm.enable_save();
            }

            else {
                
                Object.keys(frm.fields_dict).forEach(fieldname => {
                    frm.set_df_property(fieldname, "read_only", 1);
                });
                frm.disable_save();
            }
        }


		frm.trigger("show_attendance_warnings");

		// Auto-select employee field for non-HR roles
		if (
            frappe.user.has_role("Employee") &&
            !frappe.user.has_role("HR Manager") &&
            !frappe.user.has_role("Administrator") &&
            !frappe.user.has_role("Projects Manager")
        ) {
			// Hide the employee field and set current user’s employee record
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					filters: { user_id: frappe.session.user },
					fieldname: "name"
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("employee", r.message.name);
						frm.set_df_property("employee", "read_only", 1); // prevent change
					}
				}
			});
		}

		// Add the custom button
		frm.add_custom_button(__('Show Missing Attendance'), function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__('Please select Employee first.'));
				return;
			}

			frappe.call({
				method: 'hrms.hr.doctype.attendance_request.attendance_request.get_missing_attendance_html',
				args: {
					employee: frm.doc.employee
				},
				callback: function (r) {
					if (r.message) {
						const dialog = new frappe.ui.Dialog({
							title: __('Missing Attendance Details'),
							size: 'large',
							primary_action_label: __('Close'),
							primary_action() {
								dialog.hide();
							},
						});
						dialog.$wrapper.find('.modal-body').html(r.message);
						dialog.show();
					}
				}
			});
		});
	},

    show_attendance_warnings(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.dashboard.clear_headline();

			frm.call("get_attendance_warnings").then((r) => {
				if (r.message?.length) {
					frm.dashboard.reset();
					frm.dashboard.add_section(
						frappe.render_template("attendance_warnings", {
							warnings: r.message || [],
						}),
						__("Attendance Warnings"),
					);
					frm.dashboard.show();
				}
			});
		}
	},
});
