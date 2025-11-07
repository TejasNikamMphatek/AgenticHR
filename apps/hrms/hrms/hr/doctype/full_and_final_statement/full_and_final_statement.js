frappe.ui.form.on("Full and Final Statement", {
	// --- On Form Refresh ---
	refresh(frm) {
		// --- Filter hold_release_salary ---
		frm.set_query("hold_release_salary", () => ({
			filters: {
				employee: frm.doc.employee,
				salary_release: 1,
			},
		}));

		// --- Set all queries ---
		frm.events.set_employee_query(frm);
		frm.events.set_employee_assets_query(frm);
		frm.events.set_queries(frm, "payables");
		frm.events.set_queries(frm, "receivables");

		// --- Add Journal Entry button ---
		if (frm.doc.docstatus === 1 && frm.doc.status === "Unpaid") {
			frm.add_custom_button(__("Create Journal Entry"), () => {
				frm.events.create_journal_entry(frm);
			});
		}
	},

	// --- Run after full render ---
	onload_post_render(frm) {
		// Skip recalculations for submitted docs
		if (frm.doc.docstatus === 1) return;

		// Run only after all fields & child tables are rendered
		if (!frm.is_new()) {
			frm.trigger("calculate_summary");
		}
	},

	// --- Before Save ---
	before_save(frm) {
		// Prevent redundant salary fetch
		frm.doc.skip_salary_fetch = 1;

		// Clean invalid dates safely
		const date_fields = ["relieving_date", "date_of_joining", "transaction_date"];
		for (const field of date_fields) {
			const val = frm.doc[field];
			if (val && typeof val === "string" && val.toLowerCase().includes("invalid")) {
				frm.set_value(field, "");
			}
		}

		// Normalize net_pay_in_words (prevent extra spaces)
		if (frm.doc.net_pay_in_words) {
			let words = frm.doc.net_pay_in_words.trim();
			if (words !== frm.doc.net_pay_in_words) {
				frm.set_value("net_pay_in_words", words);
			}
		}
	},

	// --- On Employee Change ---
	employee(frm) {
		if (!frm.doc.employee) return;

		frm.events.get_outstanding_statements(frm);
		frm.events.set_employee_assets_query(frm);

		// Auto-link latest Employee Assets record
		frappe.db
			.get_list("Employee Assets Manage", {
				fields: ["name"],
				filters: { employee: frm.doc.employee },
				order_by: "modified desc",
				limit: 1,
			})
			.then((res) => {
				frm.set_value("employee_assets_management", res.length ? res[0].name : null);
				frm.trigger("calculate_summary");
			});
	},

	// --- Employee Query Filter ---
	set_employee_query(frm) {
		frm.set_query("employee", () => ({
			filters: {
				relieving_date: ["is", "set"],
			},
		}));
	},

	// --- Employee Assets Query Filter ---
	set_employee_assets_query(frm) {
		frm.set_query("employee_assets_management", () => {
			if (!frm.doc.employee) return {};
			return { filters: { employee: frm.doc.employee } };
		});
	},

	// --- Set Queries for Payables & Receivables ---
	set_queries(frm, table_field) {
		const doctype_map = {
			Bonus: "Additional Salary",
			"Salary Slip": "Salary Slip",
			Gratuity: "Gratuity",
			"Leave Encashment": "Leave Encashment",
			Loan: "Loan",
			"Employee Advance": "Employee Advance",
			"Expense Claim": "Expense Claim",
		};

		frm.set_query("reference_document_type", table_field, () => ({
			filters: {
				istable: 0,
				issingle: 0,
				module: ["in", ["HR", "Payroll", "Loan Management"]],
			},
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
					docstatus: 1,
				},
			};
		});
	},

	// --- Get Outstanding Statements ---
	get_outstanding_statements(frm) {
		if (!frm.doc.employee) return;
		frappe.call({
			method: "get_outstanding_statements",
			doc: frm.doc,
			callback: () => frm.refresh(),
		});
	},

	// --- Calculate Totals ---
	total_asset_recovery_cost(frm) {
		if (frm.doc.docstatus === 1) return;
		frm.trigger("calculate_total_receivable_amt");
		frm.trigger("calculate_summary");
	},

	calculate_total_payable_amt(frm) {
		if (frm.doc.docstatus === 1) return;
		let total = 0;
		(frm.doc.payables || []).forEach((row) => {
			total += flt(row.amount);
		});
		frm.set_value("total_payable_amount", total);
	},

	calculate_total_receivable_amt(frm) {
		if (frm.doc.docstatus === 1) return;
		let asset_cost = 0;
		let total_receivable = 0;

		(frm.doc.assets_allocated || []).forEach((row) => {
			if (row.action === "Recover Cost") {
				asset_cost += flt(row.cost);
			}
		});

		(frm.doc.receivables || []).forEach((row) => {
			total_receivable += flt(row.amount);
		});

		frm.set_value("total_asset_recovery_cost", asset_cost);
		frm.set_value("total_receivable_amount", asset_cost + total_receivable);
	},

	// --- Summary Calculation ---
	calculate_summary(frm) {
		if (frm.doc.docstatus === 1) return;
		frm.trigger("calculate_total_income");
		frm.trigger("calculate_total_deductions");
		frm.trigger("calculate_net_pay");
		frm.trigger("set_net_pay_in_words");
	},

	calculate_total_income(frm) {
		if (frm.doc.docstatus === 1) return;
		let total = 0;
		(frm.doc.earnings || []).forEach((row) => {
			total += flt(row.amount);
		});
		frm.set_value("total_income", total);
	},

	calculate_total_deductions(frm) {
		if (frm.doc.docstatus === 1) return;
		let total = 0;
		const allowed_components = ["Provident Fund", "Professional Tax", "ESI"];

		(frm.doc.deductions || []).forEach((row) => {
			if (allowed_components.includes(row.component)) {
				total += flt(row.amount);
			}
		});

		total += flt(frm.doc.total_asset_recovery_cost || 0);
		frm.set_value("total_deductions", total);
	},

	calculate_net_pay(frm) {
		if (frm.doc.docstatus === 1) return;
		const income = flt(frm.doc.total_income || 0);
		const deductions = flt(frm.doc.total_deductions || 0);
		const net = income - deductions;

		frm.set_value("net_pay", net);
		frm.set_value("total_payable_amount", income);
		frm.set_value("total_receivable_amount", deductions);
	},

	set_net_pay_in_words(frm) {
		if (frm.doc.docstatus === 1) return;
		if (frm.doc.net_pay && frm.doc.company) {
			frappe.call({
				method: "hrms.hr.doctype.full_and_final_statement.full_and_final_statement.get_money_in_words",
				args: {
					amount: frm.doc.net_pay,
					currency: "INR",
				},
				callback(r) {
					try {
						if (r.message) {
							frm.set_value("net_pay_in_words", r.message + " Only");
						} else {
							console.warn("Money in words empty");
							frm.set_value("net_pay_in_words", "Zero Only");
						}
					} catch (e) {
						console.error("Words Error:", e);
						frm.set_value("net_pay_in_words", "");
					}
				},
				error(r) {
					console.warn("Money call failed:", r);
					frm.set_value("net_pay_in_words", "Zero Only");
				},
			});
		} else {
			frm.set_value("net_pay_in_words", "");
		}
	},

	// --- Create Journal Entry ---
	create_journal_entry(frm) {
		frappe.call({
			method: "create_journal_entry",
			doc: frm.doc,
			callback(r) {
				if (r.message) {
					const doclist = frappe.model.sync(r.message);
					frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
				}
			},
		});
	},

	// --- Populate Earnings and Deductions ---
	populate_salary_breakup(frm, salary_slip) {
		if (!salary_slip || !frm.doc.employee) return;

		frappe.call({
			method: "hrms.hr.doctype.full_and_final_statement.full_and_final_statement.get_salary_breakup",
			args: {
				salary_slip,
				employee: frm.doc.employee,
			},
			callback(r) {
				if (r.message) {
					const { earnings, deductions } = r.message;
					frm.clear_table("earnings");
					frm.clear_table("deductions");

					(earnings || []).forEach((e) => {
						const row = frm.add_child("earnings");
						row.component = e.component || "";
						row.amount = e.amount || 0;
						row.abbr = e.abbr || "";
					});

					(deductions || []).forEach((d) => {
						const row = frm.add_child("deductions");
						row.component = d.component || "";
						row.amount = d.amount || 0;
						row.abbr = d.abbr || "";
					});

					frm.refresh_field("earnings");
					frm.refresh_field("deductions");
					frm.trigger("calculate_summary");
				}
			},
		});
	},

	// --- Fetch Notice & Leave Summary ---
	fetch_notice_leave_summary(frm, salary_slip) {
		if (!salary_slip) return;
		console.log("📡 Calling backend for slip:", salary_slip);

		frappe.call({
			method: "hrms.hr.doctype.full_and_final_statement.full_and_final_statement.get_notice_leave_summary",
			args: { salary_slip },
			freeze: true,
			freeze_message: __("Fetching Notice and Leave Summary..."),
			callback(r) {
				console.log("📦 Backend Response:", r);
				if (r.message && Object.keys(r.message).length > 0) {
					const d = r.message;
					frm.set_value("notice_period_as_per_letter", d.notice_period_as_per_letter || 30);
					frm.set_value("number_of_days_in_month", d.number_of_days_in_month || 0);
					frm.set_value("notice_period_adjustable", d.notice_period_adjustable || 0);
					frm.set_value("lop_days", d.lop_days || 0);
					frm.set_value("effective_workdays", d.effective_workdays || 0);
					frm.refresh_fields();

					frappe.show_alert({
						message: __("Notice & Leave Summary Updated"),
						indicator: "green",
					});
				} else {
					console.warn("⚠️ Empty backend response for slip:", salary_slip);
					frappe.msgprint(__("No Notice/Leave data found for selected Salary Slip. Check logs."));
				}
			},
		});
	},
});

// --- Child Table: Full and Final Outstanding Statement ---
frappe.ui.form.on("Full and Final Outstanding Statement", {
	reference_document(frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (child.reference_document_type && child.reference_document) {
			frappe.call({
				method: "hrms.hr.doctype.full_and_final_statement.full_and_final_statement.get_account_and_amount",
				args: {
					ref_doctype: child.reference_document_type,
					ref_document: child.reference_document,
					employee: frm.doc.employee,
				},
				callback(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "account", r.message[0]);
						frappe.model.set_value(cdt, cdn, "amount", r.message[1]);

						// Auto-fetch Salary Slip data
						if (child.reference_document_type === "Salary Slip") {
							console.log("🧾 Triggering Salary Slip handlers for:", child.reference_document);
							frm.events.populate_salary_breakup(frm, child.reference_document);
							frm.events.fetch_notice_leave_summary(frm, child.reference_document);
						}
					}
				},
			});
		}
	},

	amount(frm, cdt, cdn) {
		if (frm.doc.docstatus === 1) return;
		const child = locals[cdt][cdn];
		const field = child.parentfield;
		if (field === "payables") {
			frm.trigger("calculate_total_payable_amt");
		} else {
			frm.trigger("calculate_total_receivable_amt");
		}
		frm.trigger("calculate_summary");
	},
});

// --- Child Table: FNF Earnings ---
frappe.ui.form.on("FNF Earnings", {
	amount(frm) {
		if (frm.doc.docstatus === 1) return;
		frm.trigger("calculate_summary");
	},
});

// --- Child Table: FNF Deductions ---
frappe.ui.form.on("FNF Deductions", {
	amount(frm) {
		if (frm.doc.docstatus === 1) return;
		frm.set_value("net_pay_in_words", "");
		frm.trigger("calculate_summary");
	},
});

// --- Child Table: Full and Final Asset ---
frappe.ui.form.on("Full and Final Asset", {
	cost(frm) {
		if (frm.doc.docstatus === 1) return;
		frm.trigger("calculate_total_receivable_amt");
		frm.trigger("calculate_summary");
	},
});
