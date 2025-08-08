// Copyright (c) 2018, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on("Attendance Request", {
	refresh(frm) {
		frm.trigger("show_attendance_warnings");


		// Auto-select employee field for non-HR roles
		if (frappe.user.has_role("Employee") && (!frappe.user.has_role("Administrator"))) {
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
