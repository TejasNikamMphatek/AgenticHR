frappe.ui.form.on("Full and Final Statement", {
	refresh(frm) {
		// Filter hold_release_salary
		frm.set_query("hold_release_salary", () => ({
			filters: {
				employee: frm.doc.employee,
				salary_release: 1
			}
		}));

		// Set query filters
		frm.events.set_employee_query(frm);
		frm.events.set_employee_assets_query(frm);
		frm.events.set_queries(frm, "payables");
		frm.events.set_queries(frm, "receivables");

		// Add Journal Entry button
		if (frm.doc.docstatus === 1 && frm.doc.status === "Unpaid") {
			frm.add_custom_button(__("Create Journal Entry"), () => {
				frm.events.create_journal_entry(frm);
			});
		}
	},

	employee(frm) {
		frm.events.get_outstanding_statements(frm);
		frm.events.set_employee_assets_query(frm);

		if (frm.doc.employee) {
			frappe.db.get_list("Employee Assets Manage", {
				fields: ["name"],
				filters: { employee: frm.doc.employee },
				order_by: "modified desc",
				limit: 1
			}).then(res => {
				frm.set_value("employee_assets_management", res.length ? res[0].name : null);
			});
		} else {
			frm.set_value("employee_assets_management", null);
		}
	},

	set_employee_query(frm) {
		frm.set_query("employee", () => ({
			filters: { "relieving_date": ["is", "set"] }
		}));
	},

	set_employee_assets_query(frm) {
		frm.set_query("employee_assets_management", () => {
			if (!frm.doc.employee) return {};
			return { filters: { employee: frm.doc.employee } };
		});
	},

	set_queries(frm, table_field) {
		// Mapping Bonus → Additional Salary
		const doctype_map = {
			"Bonus": "Additional Salary",
			"Salary Slip": "Salary Slip",
			"Gratuity": "Gratuity",
			"Leave Encashment": "Leave Encashment",
			"Loan": "Loan",
			"Employee Advance": "Employee Advance",
			"Expense Claim": "Expense Claim"
		};

		frm.set_query("reference_document_type", table_field, () => ({
			filters: {
				istable: 0,
				issingle: 0,
				module: ["in", ["HR", "Payroll", "Loan Management"]],
			}
		}));

		frm.set_query("reference_document", table_field, (doc, cdt, cdn) => {
			const child = locals[cdt][cdn];
			const employee_filter = frm.doc.employee;

			if (!child.reference_document_type || !employee_filter) return;

			const actual_doctype = doctype_map[child.reference_document_type];
			if (!actual_doctype) return;

			return {
				filters: {
					employee: employee_filter,
					docstatus: 1
				}
			};
		});
	},

	get_outstanding_statements(frm) {
		if (frm.doc.employee) {
			frappe.call({
				method: "get_outstanding_statements",
				doc: frm.doc,
				callback: () => frm.refresh()
			});
		}
	},

	total_asset_recovery_cost(frm) {
		frm.trigger("calculate_total_receivable_amt");
	},

	calculate_total_payable_amt(frm) {
		let total = 0;
		(frm.doc.payables || []).forEach(row => {
			total += flt(row.amount, precision("amount", row));
		});
		frm.set_value("total_payable_amount", flt(total, precision("total_payable_amount")));
	},

	calculate_total_receivable_amt(frm) {
		let asset_cost = 0;
		let total_receivable = 0;

		(frm.doc.assets_allocated || []).forEach(row => {
			if (row.action === "Recover Cost") {
				asset_cost += flt(row.cost, precision("cost", row));
			}
		});

		(frm.doc.receivables || []).forEach(row => {
			total_receivable += flt(row.amount, precision("amount", row));
		});

		frm.set_value("total_asset_recovery_cost", flt(asset_cost, precision("total_asset_recovery_cost")));
		frm.set_value("total_receivable_amount", flt(asset_cost + total_receivable, precision("total_receivable_amount")));
	},

	create_journal_entry(frm) {
		frappe.call({
			method: "create_journal_entry",
			doc: frm.doc,
			callback(r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	}
});

frappe.ui.form.on("Full and Final Outstanding Statement", {
	reference_document(frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (child.reference_document_type && child.reference_document) {
			frappe.call({
				method: "hrms.hr.doctype.full_and_final_statement.full_and_final_statement.get_account_and_amount",
				args: {
					ref_doctype: child.reference_document_type,
					ref_document: child.reference_document,
					employee: frm.doc.employee
				},
				callback(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "account", r.message[0]);
						frappe.model.set_value(cdt, cdn, "amount", r.message[1]);
					}
				}
			});
		}
	},

	amount(frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		const field = child.parentfield;
		if (field === "payables") {
			frm.trigger("calculate_total_payable_amt");
		} else {
			frm.trigger("calculate_total_receivable_amt");
		}
	}
});

frappe.ui.form.on("Full and Final Asset", {
	cost(frm) {
		frm.trigger("calculate_total_receivable_amt");
	}
});
