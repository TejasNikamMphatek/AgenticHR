// Copyright (c) 2021, mPHATEK Systems Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Exit Interview", {
	refresh: function (frm) {
		if (
			!frm.doc.__islocal &&
			!frm.doc.questionnaire_email_sent &&
			frappe.boot.user.can_write.includes("Exit Interview")
		) {
			frm.add_custom_button(__("Send Exit Questionnaire"), function () {
				frm.trigger("send_exit_questionnaire");
			});
		}

		// Set query here so frm is defined
        frm.set_query("ref_doctype", function () {
            return {
                filters: {
                    employee: frm.doc.employee
                }
            };
        });
	},

	employee: function (frm) {
		frappe.db.get_value("Employee", frm.doc.employee, "relieving_date", (message) => {
			if (!message.relieving_date) {
				frappe.throw({
					message: __("Please set the relieving date for employee {0}", [
						'<a href="/app/employee/' +
							frm.doc.employee +
							'">' +
							frm.doc.employee +
							"</a>",
					]),
					title: __("Relieving Date Missing"),
				});
			}
		});
	},

	send_exit_questionnaire: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.exit_interview.exit_interview.send_exit_questionnaire",
			args: {
				interviews: [frm.doc],
			},
			callback: function (r) {
				if (!r.exc) {
					frm.refresh_field("questionnaire_email_sent");
				}
			},
		});
	},
});
