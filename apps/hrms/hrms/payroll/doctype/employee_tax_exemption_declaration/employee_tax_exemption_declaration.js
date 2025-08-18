frappe.ui.form.on("Employee Tax Exemption Declaration", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			// Admin or HR can choose from all employees
			if (
				frappe.user.has_role("HR Manager") ||
				frappe.user.has_role("HR User") ||
				frappe.session.user === "Administrator"
			) {
				return {
					filters: {
						status: "Active"
					}
				};
			} else {
				// Normal users can only see themselves
				return {
					filters: {
						status: "Active",
						user_id: frappe.session.user
					}
				};
			}
		});

		frm.set_query("payroll_period", function () {
			const fields = { employee: "Employee", company: "Company" };
			for (let [field, label] of Object.entries(fields)) {
				if (!frm.doc[field]) {
					frappe.msgprint(__("Please select {0}", [label]));
				}
			}
			if (frm.doc.employee && frm.doc.company) {
				return {
					filters: {
						company: frm.doc.company,
					},
				};
			}
		});

		frm.set_query("exemption_sub_category", "declarations", function () {
			return {
				filters: {
					is_active: 1,
				},
			};
		});
	},

	refresh: function (frm) {
		// Only auto-fill employee for non-HR users
		if (
			!frappe.user.has_role("HR Manager") &&
			!frappe.user.has_role("HR User") &&
			frappe.session.user !== "Administrator"
		) {
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
						frm.set_df_property("employee", "read_only", 1); // make it read-only
					}
				}
			});
		} else {
			// HR/Admin can select manually
			frm.set_df_property("employee", "read_only", 0);
		}

		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Submit Proof"), function () {
				frappe.model.open_mapped_doc({
					method: "hrms.payroll.doctype.employee_tax_exemption_declaration.employee_tax_exemption_declaration.make_proof_submission",
					frm: frm,
				});
			}).addClass("btn-primary");
		}
	},

	employee: function (frm) {
		if (frm.doc.employee) {
			frm.trigger("get_employee_currency");
		}
	},

	get_employee_currency: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("currency", r.message);
					frm.refresh_fields();
				}
			},
		});
	},
});
