# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd.
# For license information, please see license.txt

import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import (
    flt, get_link_to_form, today, getdate, money_in_words,
    date_diff, add_months, get_last_day
)
from erpnext.setup.doctype.employee.employee import get_employee_emails


class FullandFinalStatement(Document):

    # -----------------------
    # DocType lifecycle hooks
    # -----------------------
    def before_insert(self):
        """Populate base outstanding statements when new FNF is first created"""
        try:
            self.get_outstanding_statements()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "FNF.before_insert")
    def before_save(self):
        try:
            if frappe.utils.cint(getattr(self, "skip_salary_fetch", 0)) == 1:
                frappe.logger().info("⏩ Skipping heavy fetch during save")
                self.set_totals()
                self.set_net_pay_in_words()
                return
            self.get_outstanding_statements()
            self.get_employment_summary()
            self.calculate_notice_leave()
            self.pull_salary_components()
            self.set_totals()
            self.set_net_pay_in_words()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "FNF.before_save_failed")

    # def before_save(self):
    #     # 🧹 ALWAYS purge rogue fields first (before any skips/returns)
    #     rogue_fields = ['float_deh']  # Add more if they respawn
    #     for field in rogue_fields:
    #         if hasattr(self, field):
    #             delattr(self, field)
    #             frappe.logger().info(f"🧹 Purged rogue: {field} from {self.name}")

    #     if frappe.utils.cint(getattr(self, "skip_salary_fetch", 0)) == 1:
    #         frappe.logger().info("⏩ [FNF] Skipping auto-fetch (skip_salary_fetch flag set).")
    #         # Run lightweight totals/words for safety
    #         self.set_totals()
    #         self.set_net_pay_in_words()
    #         return

    #     # ✅ Standard processing (when not skipped)
    #     self.get_outstanding_statements()
    #     self.get_employment_summary()
    #     self.calculate_notice_leave()
    #     self.pull_salary_components()
    #     self.set_totals()
    #     self.set_net_pay_in_words()
    
    def validate(self):
        """
        Validate consistency and ensure required data before submission.
        """
        # ✅ Optional: If skip flag is set (just for safety)
        if getattr(self, "skip_salary_fetch", 0):
            frappe.logger().info("⏩ Validation skipped salary fetch section (client save flag active)")
            # Don’t return here, we still validate data integrity
            pass

        self.validate_relieving_date()

        if not self.resignation_submission_date:
            frappe.throw(_("Set Submission Date of Resignation"))

        # Ensure all unsettled rows are cleared (only if status field exists in children)
        for table in ['earnings', 'deductions']:
            for row in self.get(table, []):
                if row.get("status") == "Unsettled" and flt(row.amount) > 0:
                    frappe.throw(_(
                        "Settle {0} row {1} ({2}) before submission"
                    ).format(table, row.component, row.amount))

        self.validate_settlement("payables")
        self.validate_settlement("receivables")
        # self.validate_assets()  # enable if strict asset validation required

        # 🛠️ FIXED: Fully remove this—redundant with JS whitelisted call
        # No need for backend fetch_notice_leave_summary(); fields are set client-side
        # if hasattr(self, 'salary_slip') and self.salary_slip:
        #     self.fetch_notice_leave_summary()  # Gone—no AttributeError!

    def before_submit(self):
        self.validate_settlement("payables")
        self.validate_settlement("receivables")

    def on_submit(self):
        # mark employee as Left and email slip
        try:
            employee = frappe.get_doc("Employee", self.employee)
            employee.status = "Left"
            employee.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "FNF.on_submit - employee status")
        #self.email_fnf_slip()

    def on_cancel(self):
        try:
            employee = frappe.get_doc("Employee", self.employee)
            employee.status = "Active"
            employee.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "FNF.on_cancel - employee status")

    # -----------------------
    # Validation helpers
    # -----------------------
    def validate_relieving_date(self):
        if not self.relieving_date:
            frappe.throw(
                _("Please set {0} for Employee {1}").format(
                    bold(_("Relieving Date")),
                    get_link_to_form("Employee", self.employee),
                ),
                title=_("Missing Relieving Date"),
            )

    def validate_settlement(self, component_type):
        unsettled_rows = []
        for data in self.get(component_type, []):
            if flt(getattr(data, "amount", 0)) > 0 and getattr(data, "status", "Unsettled") == "Unsettled":
                unsettled_rows.append(f"{data.component or data.reference_document_type} (₹{data.amount})")
        if unsettled_rows:
            frappe.throw(
                _("Settle all {0} before submission: {1}").format(
                    component_type.title(), ", ".join(unsettled_rows)
                ),
                title=_("Unsettled Transactions"),
            )

    def validate_assets(self):
        pending_returns = []
        for data in self.get("assets_allocated", []):
            if data.action == "Return":
                if data.status == "Owned":
                    pending_returns.append(_("Row {0}: {1}").format(data.idx, bold(data.asset_name)))
            elif data.action == "Recover Cost":
                data.status = "Owned"
        if pending_returns:
            msg = _("All allocated assets should be returned before submission") + "<br><br>" + ", ".join(pending_returns)
            frappe.throw(msg, title=_("Pending Asset Returns"))

    # -----------------------
    # Outstanding statements
    # -----------------------
    @frappe.whitelist()
    def get_outstanding_statements(self):
        if not self.relieving_date:
            frappe.throw(
                _("Set Relieving Date for Employee: {0}").format(get_link_to_form("Employee", self.employee))
            )

        if not len(self.get("payables", [])):
            components = self.get_payable_component()
            self.create_component_row(components, "payables")

        if not len(self.get("receivables", [])):
            components = self.get_receivable_component()
            self.create_component_row(components, "receivables")

        self.get_assets_statements()

    # compatibility redirect (some JS might call doc.fetch_outstanding_components())
    @frappe.whitelist()
    def fetch_outstanding_components(self):
        return self.get_outstanding_statements()

    def get_assets_statements(self):
        if not len(self.get("assets_allocated", [])):
            for data in self.get_assets_movement():
                self.append("assets_allocated", data)

    def set_total_asset_recovery_cost(self):
        # compute if you store it elsewhere; placeholder sets zero safely
        total_cost = 0
        # optionally sum self.assets_allocated where action == "Recover Cost"
        for a in self.get("assets_allocated", []):
            if getattr(a, "action", "") == "Recover Cost":
                total_cost += flt(getattr(a, "cost", 0))
        self.total_asset_recovery_cost = flt(total_cost, self.precision("total_asset_recovery_cost"))

    def create_component_row(self, components, component_type):
        for component in components:
            child = self.append(component_type, {})
            child.status = "Unsettled"
            child.reference_document_type = component if component != "Bonus" else "Additional Salary"
            child.component = component
            if component_type == "receivables" and not child.reference_document:
                child.status = "Settled"  # Auto-settle empty receivables

    def get_payable_component(self):
        return [
            "Salary Slip",
            "Gratuity",
        ]

    def get_receivable_component(self):
        return [
            "Employee Advance",
        ]

    # -----------------------
    # Asset movement helper
    # -----------------------
    def get_assets_movement(self):
        asset_movements = frappe.get_all(
            "Asset Movement Item",
            filters={"docstatus": 1},
            fields=["asset", "from_employee", "to_employee", "parent", "asset_name"],
            or_filters={"from_employee": self.employee, "to_employee": self.employee},
        )

        data = []
        inward_movements = []
        outward_movements = []
        for movement in asset_movements:
            if movement.to_employee and movement.to_employee == self.employee:
                inward_movements.append(movement)
            if movement.from_employee and movement.from_employee == self.employee:
                outward_movements.append(movement)

        for movement in inward_movements:
            outwards_count = [m.asset for m in outward_movements].count(movement.asset)
            inwards_counts = [m.asset for m in inward_movements].count(movement.asset)
            if inwards_counts > outwards_count:
                cost = frappe.db.get_value("Asset", movement.asset, "total_asset_cost")
                data.append({
                    "reference": movement.parent,
                    "asset_name": movement.asset_name,
                    "date": frappe.db.get_value("Asset Movement", movement.parent, "transaction_date"),
                    "actual_cost": cost,
                    "cost": cost,
                    "action": "Return",
                    "status": "Owned",
                })
        return data

    # -----------------------
    # Employment summary + notice
    # -----------------------
    @frappe.whitelist()
    def get_employment_summary(self):
        # This method can be called from client as a doc method (frappe.call with run_doc_method)
        emp = frappe.get_doc("Employee", self.employee)
        self.employee_name = emp.employee_name
        self.designation = emp.designation
        self.department = emp.department
        self.location = emp.branch or "Pune"
        self.date_of_joining = emp.date_of_joining
        self.relieving_date = emp.relieving_date
        self.company = emp.company

        # Last Salary Paid (format month year)
        last_ss = frappe.db.sql("""
            SELECT end_date FROM `tabSalary Slip` 
            WHERE employee = %s AND docstatus = 1 ORDER BY end_date DESC LIMIT 1
        """, self.employee, as_dict=1)
        self.last_salary_paid = last_ss[0].end_date.strftime("%b %Y") if last_ss else ""

        # Resignation Date
        self.resignation_submission_date = frappe.db.get_value("Employee Separation", {"employee": self.employee, "docstatus": 1}, "resignation_letter_date") or today()

    def calculate_notice_leave(self):
        # Internal doc method (keeps same name as your original)
        sep = frappe.get_doc("Employee Separation", {"employee": self.employee, "docstatus": 1}) if frappe.db.exists("Employee Separation", {"employee": self.employee}) else None
        if sep:
            self.notice_period_as_per_letter = flt(getattr(sep, "notice_period_days", 30))
            self.notice_period_adjustable = flt(getattr(sep, "notice_adjustment_days", 0))
            self.pl_days_payable = flt(getattr(sep, "pending_leave_days", 0))
            self.lop_days = flt(getattr(sep, "lop_days", 0))
        else:
            self.notice_period_as_per_letter = 30
            self.notice_period_adjustable = 0
            self.pl_days_payable = 0
            self.lop_days = 0

        # compute month days and effective workdays safely
        try:
            month_start = getdate(self.relieving_date.replace(day=1))
            month_end = get_last_day(month_start)
            self.number_of_days_in_month = date_diff(month_end, month_start) + 1
            self.effective_workdays = self.number_of_days_in_month - self.lop_days - (self.notice_period_as_per_letter - self.notice_period_adjustable)
        except Exception:
            # if relieving_date missing or invalid, fallback to defaults
            self.number_of_days_in_month = 30
            self.effective_workdays = 30 - self.lop_days

    # Allow client to call notice calculation as a module function too
    @frappe.whitelist()
    def calculate_notice_leave_wh(self):
        # wrapper to call the instance method (for run_doc_method or plain call)
        return self.calculate_notice_leave()

    # -----------------------
    # Salary components
    # -----------------------
    @frappe.whitelist()
    def pull_salary_components(self):
        """
        Fetch salary components from Salary Slip or Structure Assignment.
        Now respects skip_salary_fetch flag — never overwrites manual earnings/deductions.
        """
        # 🚫 Safety guard
        if frappe.utils.cint(getattr(self, "skip_salary_fetch", 0)) == 1:
            frappe.msgprint(_("Skipped auto-fetch from Salary Slip (manual mode enabled)."))
            frappe.logger().info("⏩ [FNF] pull_salary_components aborted — skip_salary_fetch flag active.")
            return

        # ✅ Proceed only when allowed
        if not self.employee:
            frappe.throw(_("Please select an Employee before fetching components."))

        prorate = (
            flt(self.effective_workdays) / flt(self.number_of_days_in_month)
            if self.number_of_days_in_month else 1
        )

        # Priority 1: Recent Salary Slip (auto or selected)
        recent_slip = getattr(self, "recent_salary_slip", None) or self._get_latest_salary_slip()
        if recent_slip:
            slip = frappe.get_doc("Salary Slip", recent_slip)
            self.set("earnings", [])  # Clear
            self.set("deductions", [])

            # Earnings from Slip's Salary Detail (prorate for effective days)
            for detail in slip.get("earnings", []):
                amt = flt(detail.amount) * prorate  # Prorate
                if amt:
                    self.append("earnings", {
                        "component": detail.salary_component,
                        "amount": amt,
                        "abbr": getattr(detail, "abbr", "") or "",
                        "status": "Settled"
                    })

            # Deductions from Slip
            for detail in slip.get("deductions", []):
                amt = flt(detail.amount) * prorate
                if amt:
                    self.append("deductions", {
                        "component": detail.salary_component,
                        "amount": amt,
                        "abbr": getattr(detail, "abbr", "") or "",
                        "status": "Settled"
                    })

            frappe.msgprint(_("Components fetched from Salary Slip {0} (prorated {1}%).").format(recent_slip, flt(prorate*100)))
            self.set_totals()
            return

        # Fallback: Salary Structure Assignment
        ssa = frappe.db.get_value("Salary Structure Assignment", {"employee": self.employee, "docstatus": 1}, "salary_structure", order_by="from_date desc")
        if ssa:
            struct = frappe.get_doc("Salary Structure", ssa)
            self.set("earnings", [])
            self.set("deductions", [])

            # Earnings
            for row in struct.get("earnings", []):
                amt = flt(row.amount) * prorate
                abbr = frappe.db.get_value("Salary Component", row.salary_component, "salary_component_abbr") or ""
                if amt:
                    self.append("earnings", {"component": row.salary_component, "amount": amt, "abbr": abbr, "status": "Settled"})

            # Hold Salary (if provided)
            if getattr(self, "hold_release_salary", None):
                try:
                    hold_doc = frappe.get_doc("Hold Salary Employee", self.hold_release_salary)
                    hold_amount = flt(getattr(hold_doc, "hold_amount", 0))
                    if hold_amount:
                        self.append("earnings", {"component": "Hold Salary", "amount": hold_amount, "abbr": "HS", "status": "Settled"})
                except Exception:
                    frappe.log_error(frappe.get_traceback(), "FNF.pull_salary_components - hold_salary")

            # Leave Encashment (basic-based)
            try:
                daily_rate = flt(struct.base or 0) / 30
                if flt(getattr(self, "pl_days_payable", 0)):
                    self.append("earnings", {"component": "Leave Encashment", "amount": flt(self.pl_days_payable) * daily_rate, "abbr": "LE", "status": "Settled"})
            except Exception:
                pass

            # Deductions
            for row in struct.get("deductions", []):
                amt = flt(row.amount) * prorate
                abbr = frappe.db.get_value("Salary Component", row.salary_component, "salary_component_abbr") or ""
                if amt:
                    self.append("deductions", {"component": row.salary_component, "amount": amt, "abbr": abbr, "status": "Settled"})

            # Merge settled payables/receivables into earnings/deductions
            for p in self.get("payables", []):
                if flt(getattr(p, "amount", 0)) > 0 and getattr(p, "status", "") == "Settled":
                    abbr = (getattr(p, "reference_document", "") or "")[:10]
                    self.append("earnings", {"component": p.component or p.reference_document_type, "amount": p.amount, "abbr": abbr, "status": "Settled"})

            for r in self.get("receivables", []):
                if flt(getattr(r, "amount", 0)) > 0 and getattr(r, "status", "") == "Settled":
                    abbr = (getattr(r, "reference_document", "") or "")[:10]
                    self.append("deductions", {"component": r.component or r.reference_document_type, "amount": r.amount, "abbr": abbr, "status": "Settled"})

            if flt(getattr(self, "total_asset_recovery_cost", 0)) > 0:
                self.append("deductions", {"component": "Asset Recovery Cost", "amount": self.total_asset_recovery_cost, "abbr": "AR", "status": "Settled"})

            self.set_totals()
        else:
            frappe.msgprint(_("No Salary Slip or Structure—add fallback."))

    def _get_latest_salary_slip(self):
        # Auto-select latest submitted Slip for employee
        latest = frappe.db.get_value("Salary Slip", {"employee": self.employee, "docstatus": 1}, "name", order_by="posting_date desc")
        if latest:
            self.recent_salary_slip = latest  # set if not set
        return latest

    # -----------------------
    # Totals & words
    # -----------------------
    def set_totals(self):
        allowed = {"provident fund", "professional tax", "esi"}

        self.total_income = sum(flt(row.amount) for row in self.get("earnings", []))
        def deduction_allowed(row):
            comp = (getattr(row, "component", "") or "").strip().lower()
            abbr = (getattr(row, "abbr", "") or "").strip().lower()
        # also accept common abbreviations e.g. "pf", "pt", "esi"
            return comp in allowed or abbr in {"pf", "pt", "esi"}
        total_deductions_from_rows = sum(
        flt(row.amount) for row in self.get("deductions", []) if deduction_allowed(row)
    )   
        asset_recovery = flt(getattr(self, "total_asset_recovery_cost", 0))
        self.total_deductions = total_deductions_from_rows + asset_recovery
        #self.total_deductions = sum(flt(row.amount) for row in self.get("deductions", [])) + flt(getattr(self, "total_asset_recovery_cost", 0))
        self.net_pay = flt(self.total_income - self.total_deductions)
        self.total_payable_amount = self.total_income
        self.total_receivable_amount = self.total_deductions

    def set_net_pay_in_words(self):
        if self.net_pay:
            currency = frappe.db.get_value("Company", self.company, "default_currency") or "INR"
            self.net_pay_in_words = money_in_words(self.net_pay, currency) + " Only"
        else:
            self.net_pay_in_words = ""

    # -----------------------
    # Email & Journal
    # -----------------------
    
    def email_fnf_slip(self):
        
        
        try:
            receiver = get_employee_emails([self.employee]) if isinstance(self.employee, str) else get_employee_emails(self.employee)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "FNF.email_fnf_slip - get_employee_emails failed")
            receiver = []

        if not receiver:
            frappe.logger().warning(f"⚠️ No valid email found for employee {self.employee}")
            return
        payroll_settings = frappe.get_single("Payroll Settings")
        subject = f"FNF Settlement - {self.employee_name}"
        message = _("Your Full and Final Settlement is attached. Net: {0}").format(self.net_pay_in_words)
        password = None
        if payroll_settings.encrypt_salary_slips_in_emails:
            password = (self.employee_name or "")[:8]
            message += _("<br>PDF password: {0}").format(password)
        try:
            pdf = frappe.get_print(self.doctype, self.name, "FNF Settlement Slip", password=password)
            attachments = [{'fname': f'FNF_{self.name}.pdf', 'fcontent': pdf}]
            frappe.sendmail(recipients=receiver, subject=subject, message=message, attachments=attachments)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "FNF.email_fnf_slip")

    @frappe.whitelist()
    def create_journal_entry(self):
        precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency") or 2
        jv = frappe.new_doc("Journal Entry")
        jv.company = self.company
        jv.voucher_type = "Bank Entry"
        jv.posting_date = today()
        jv.user_remark = f"FNF for {self.employee_name} - Net {self.net_pay} (Ref: {self.name})"

        # Debits: earnings
        for row in self.get("earnings", []):
            if flt(row.amount) > 0:
                account = frappe.db.get_value("Salary Component", row.component, "default_account") or \
                          frappe.db.get_value("Company", self.company, "default_payroll_payable_account")
                jv.append("accounts", {
                    "account": account,
                    "debit_in_account_currency": flt(row.amount, precision),
                    "user_remark": f"{row.component} - {self.name}",
                    "party_type": "Employee",
                    "party": self.employee,
                    "reference_type": self.doctype,
                    "reference_name": self.name
                })

        # Credits: deductions
        for row in self.get("deductions", []):
            if flt(row.amount) > 0:
                account = frappe.db.get_value("Salary Component", row.component, "default_account") or \
                          frappe.db.get_value("Company", self.company, "default_employee_advance_account")
                jv.append("accounts", {
                    "account": account,
                    "credit_in_account_currency": flt(row.amount, precision),
                    "user_remark": f"{row.component} - {self.name}",
                    "party_type": "Employee",
                    "party": self.employee,
                    "reference_type": self.doctype,
                    "reference_name": self.name
                })

        # Balance net_pay
        if flt(self.net_pay) != 0:
            net_abs = abs(self.net_pay)
            balance_account = frappe.db.get_value("Company", self.company, "default_bank_account") or "Cash - " + self.company
            side = "credit_in_account_currency" if self.net_pay > 0 else "debit_in_account_currency"
            jv.append("accounts", {
                side: net_abs,
                "account": balance_account,
                "user_remark": f"Net FNF Balance - {self.name}",
                "reference_type": self.doctype,
                "reference_name": self.name
            })

        return jv


# -----------------------
# Module-level helpers (whitelisted) for client JS calls
# -----------------------
@frappe.whitelist()
def fetch_outstanding_components(employee=None):
    """
    Safe wrapper: return empty structure if employee not provided.
    """
    if not employee:
        # return empty structure (JS will handle empty lists)
        return {"payables": [], "receivables": []}

    data = {"payables": [], "receivables": []}

    # Salary Slips (example)
    slips = frappe.get_all("Salary Slip", filters={"employee": employee, "docstatus": 1}, fields=["name", "net_pay"])
    for s in slips:
        data["payables"].append({
            "component": "Salary Slip",
            "reference_doctype": "Salary Slip",
            "reference_name": s.name,
            "amount": flt(s.net_pay),
            "status": "Unsettled"
        })

    # Expense Claim example
    claims = frappe.get_all("Expense Claim", filters={"employee": employee, "docstatus": 1, "status": ["in", ["Unpaid", "Approved"]]}, fields=["name", "grand_total"])
    for c in claims:
        data["payables"].append({
            "component": "Expense Claim",
            "reference_doctype": "Expense Claim",
            "reference_name": c.name,
            "amount": flt(c.grand_total),
            "status": "Unsettled"
        })

    # Loans example
    loans = frappe.get_all("Loan", filters={"applicant": employee, "docstatus": 1}, fields=["name","total_payment","total_amount_paid"])
    for l in loans:
        amount = flt(l.total_payment) - flt(l.total_amount_paid)
        if amount:
            data["receivables"].append({
                "component": "Loan",
                "reference_doctype": "Loan",
                "reference_name": l.name,
                "amount": amount,
                "status": "Unsettled"
            })

    return data


@frappe.whitelist()
def get_employment_summary(employee=None):
    """Module-level wrapper to return employment summary for client JS"""
    if not employee:
        frappe.throw(_("Employee is required"))
    emp = frappe.get_doc("Employee", employee)
    last_ss = frappe.db.sql("""
        SELECT end_date FROM `tabSalary Slip`
        WHERE employee = %s AND docstatus = 1
        ORDER BY end_date DESC LIMIT 1
    """, employee, as_dict=1)
    last_salary_paid = last_ss[0].end_date.strftime("%b %Y") if last_ss else ""
    return {
        "employee_name": emp.employee_name,
        "designation": emp.designation,
        "department": emp.department,
        "date_of_joining": emp.date_of_joining,
        "relieving_date": emp.relieving_date,
        "company": emp.company,
        "last_salary_paid": last_salary_paid
    }


@frappe.whitelist()
def calculate_notice_leave(employee=None, relieving_date=None):
    """Module-level wrapper to calculate notice / leave deductions for client JS"""
    if not employee:
        frappe.throw(_("Employee is required"))

    sep = frappe.get_doc("Employee Separation", {"employee": employee, "docstatus": 1}) if frappe.db.exists("Employee Separation", {"employee": employee}) else None
    notice_period = flt(getattr(sep, "notice_period_days", 30)) if sep else 30
    notice_adjust = flt(getattr(sep, "notice_adjustment_days", 0)) if sep else 0
    lop_days = flt(getattr(sep, "lop_days", 0)) if sep else 0
    pending_leave_days = flt(getattr(sep, "pending_leave_days", 0)) if sep else 0

    # determine month length and effective workdays (use relieving_date param if provided)
    rel_date = getdate(relieving_date) if relieving_date else (getdate(sep.relieving_date) if sep and sep.relieving_date else None)
    if rel_date:
        month_start = getdate(rel_date.replace(day=1))
        month_end = get_last_day(month_start)
        number_of_days_in_month = date_diff(month_end, month_start) + 1
    else:
        number_of_days_in_month = 30

    effective_workdays = number_of_days_in_month - lop_days - (notice_period - notice_adjust)

    return {
        "notice_period_as_per_letter": notice_period,
        "notice_period_adjustable": notice_adjust,
        "lop_days": lop_days,
        "pl_days_payable": pending_leave_days,
        "number_of_days_in_month": number_of_days_in_month,
        "effective_workdays": effective_workdays
    }


# Utility function used in earlier code
@frappe.whitelist()
def get_account_and_amount(ref_doctype, ref_document, employee=None):
    if not ref_doctype or not ref_document:
        return None

    # Salary Slip
    if ref_doctype == "Salary Slip":
        salary_details = frappe.db.get_value(
            "Salary Slip", ref_document, ["payroll_entry", "net_pay", "employee"], as_dict=1
        )
        if employee and salary_details and salary_details.employee != employee:
            frappe.throw(_("Selected Salary Slip does not belong to employee {0}").format(employee))

        amount = salary_details.net_pay if salary_details else 0
        payable_account = (
            frappe.db.get_value("Payroll Entry", salary_details.payroll_entry, "payroll_payable_account")
            if salary_details and salary_details.payroll_entry
            else None
        )
        return [payable_account, amount]

    # Gratuity
    if ref_doctype == "Gratuity":
        details = frappe.db.get_value(
            "Gratuity", ref_document, ["payable_account", "amount", "employee"], as_dict=1
        )
        if employee and details and details.employee != employee:
            frappe.throw(_("Selected Gratuity does not belong to employee {0}").format(employee))
        return [details.payable_account, details.amount] if details else [None, 0]

    # Leave Encashment
    if ref_doctype == "Leave Encashment":
        details = frappe.db.get_value(
            "Leave Encashment",
            ref_document,
            ["employee", "encashment_amount"],
            as_dict=1,
        )

        if employee and details and details.employee != employee:
            frappe.throw(_("Selected Leave Encashment does not belong to employee {0}").format(employee))
        payable_account = ""
        amount = details.encashment_amount if details else 0
        return [payable_account, amount]

    # Expense Claim
    if ref_doctype == "Expense Claim":
        details = frappe.db.get_value(
            "Expense Claim",
            ref_document,
            ["payable_account", "grand_total", "total_amount_reimbursed", "total_advance_amount", "employee"],
            as_dict=1,
        )
        if employee and details and details.employee != employee:
            frappe.throw(_("Selected Expense Claim does not belong to employee {0}").format(employee))
        if not details:
            return [None, 0]
        payable_account = details.payable_account
        amount = flt(details.grand_total) - (flt(details.total_amount_reimbursed) + flt(details.total_advance_amount))
        return [payable_account, amount]

    # Loan
    if ref_doctype == "Loan":
        details = frappe.db.get_value(
            "Loan", ref_document, ["payment_account", "total_payment", "total_amount_paid", "employee"], as_dict=1
        )
        if employee and details and details.employee != employee:
            frappe.throw(_("Selected Loan does not belong to employee {0}").format(employee))
        if not details:
            return [None, 0]
        payment_account = details.payment_account
        amount = flt(details.total_payment) - flt(details.total_amount_paid)
        return [payment_account, amount]

    # Employee Advance
    if ref_doctype == "Employee Advance":
        details = frappe.db.get_value(
            "Employee Advance",
            ref_document,
            ["advance_account", "paid_amount", "claimed_amount", "return_amount", "employee"],
            as_dict=1,
        )
        if employee and details and details.employee != employee:
            frappe.throw(_("Selected Employee Advance does not belong to employee {0}").format(employee))
        if not details:
            return [None, 0]
        payment_account = details.advance_account
        amount = flt(details.paid_amount) - (flt(details.claimed_amount) + flt(details.return_amount))
        return [payment_account, amount]


def update_full_and_final_statement_status(doc, method=None):
    """Updates FnF status on Journal Entry Submission/Cancellation"""
    status = "Paid" if doc.docstatus == 1 else "Unpaid"

    for entry in doc.get("accounts", []):
        if getattr(entry, "reference_type", "") == "Full and Final Statement":
            try:
                frappe.db.set_value("Full and Final Statement", entry.reference_name, "status", status)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "update_full_and_final_statement_status")


@frappe.whitelist()
def get_salary_breakup(salary_slip, employee):
    """
    Return earnings/deductions lists with fields:
      - component  (the Salary Component name, suitable for the child field 'component')
      - amount
      - abbr  (optional)
    """
    if not salary_slip or not employee:
        return {"earnings": [], "deductions": []}

    slip = frappe.get_doc("Salary Slip", salary_slip)
    if not slip:
        return {"earnings": [], "deductions": []}

    # ensure slip belongs to employee
    if getattr(slip, "employee", None) and slip.employee != employee:
        frappe.throw(_("Selected Salary Slip does not belong to the Employee"))

    earnings = []
    for e in slip.get("earnings", []):
        comp_name = e.salary_component
        abbr = frappe.db.get_value("Salary Component", comp_name, "salary_component_abbr") or ""
        earnings.append({
            "component": comp_name,
            "amount": flt(e.amount),
            "abbr": abbr
        })

    deductions = []
    for d in slip.get("deductions", []):
        comp_name = d.salary_component
        abbr = frappe.db.get_value("Salary Component", comp_name, "salary_component_abbr") or ""
        deductions.append({
            "component": comp_name,
            "amount": flt(d.amount),
            "abbr": abbr
        })

    return {"earnings": earnings, "deductions": deductions}


@frappe.whitelist()
def get_notice_leave_summary(salary_slip=None, **kwargs):
    """Fetch Notice and Leave Summary from selected Salary Slip and related Employee Separation/Employee"""
    try:
        # --- Defaults (non-empty base)
        response = {
            "notice_period_as_per_letter": 30,
            "number_of_days_in_month": 30,
            "notice_period_adjustable": 0,
            "lop_days": 0,
            "effective_workdays": 30,
        }

        if not salary_slip:
            frappe.log_error("Missing salary_slip", "FNF get_notice_leave_summary")
            return response

        # --- Fetch Slip
        slip_fields = ["employee", "total_working_days", "leave_without_pay", "absent_days", "payment_days", "end_date"]
        slip = frappe.db.get_value("Salary Slip", salary_slip, slip_fields, as_dict=True)
        frappe.logger().info(f"[FNF] Slip {salary_slip}: {slip}")

        if not slip:
            return response

        # --- Update from Slip (real data!)
        num_days = flt(slip.total_working_days or 0)
        lwp = flt(slip.leave_without_pay or 0)
        absent = flt(slip.absent_days or 0)  # Key: Add absent_days
        lop_total = lwp + absent  # Now 0 + 1 = 1
        payment = flt(slip.payment_days or 0)
        effective = payment if payment > 0 else max(0, num_days - lop_total)  # Prioritize payment=2, fallback 30-1=29

        # Fallback num_days to calendar if 0
        if num_days == 0 and slip.end_date:
            from frappe.utils import get_last_day, date_diff, getdate
            month_start = getdate(slip.end_date.replace(day=1))
            month_end = get_last_day(month_start)
            num_days = date_diff(month_end, month_start) + 1

        response.update({
            "number_of_days_in_month": num_days,  # 30
            "lop_days": lop_total,                # 1
            "effective_workdays": effective,      # 2 (from payment)
        })

        frappe.logger().info(f"[FNF] Computed from slip: LOP={lop_total}, Effective={effective}")

        # --- Separation (handle standard/missing fields)
        sep_exists = frappe.db.exists("Employee Separation", {"employee": slip.employee, "docstatus": 1})
        if sep_exists:
            sep = frappe.get_doc("Employee Separation", {"employee": slip.employee, "docstatus": 1})
            # Standard HRMS fields: Use 'pending_leave_days' for LOP if present, else skip
            # Custom: Add 'notice_period_days', etc. (see Step 3)
            sep_dict = {
                "notice_period_days": getattr(sep, "notice_period_days", 0),  # Safe getattr
                "notice_adjustment_days": getattr(sep, "notice_adjustment_days", 0),
                "lop_days": getattr(sep, "lop_days", getattr(sep, "pending_leave_days", 0)),  # Fallback to pending_leave
            }
            if any(sep_dict.values()):  # Only update if data
                response["notice_period_as_per_letter"] = flt(sep_dict["notice_period_days"] or 30)
                response["notice_period_adjustable"] = flt(sep_dict["notice_adjustment_days"])
                response["lop_days"] = max(response["lop_days"], flt(sep_dict["lop_days"]))  # Merge with slip LOP
                frappe.logger().info(f"[FNF] From Separation: {sep_dict}")
        else:
            frappe.logger().info(f"[FNF] No Separation for {slip.employee}")

        # --- Employee Fallback (safe)
        try:
            emp_notice = flt(frappe.db.get_value("Employee", slip.employee, "notice_number_of_days") or 30)
            if emp_notice != 30:  # Only if custom field exists
                response["notice_period_as_per_letter"] = emp_notice
        except:
            pass  # Ignore missing field

        frappe.logger().info(f"[FNF] Final for {salary_slip}: {response}")
        return response

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "FNF get_notice_leave_summary Failed")
        return response  # Defaults

# --- Whitelisted wrapper for money_in_words (fixes 403) ---
@frappe.whitelist()
def get_money_in_words(amount, currency="INR"):
    """Whitelisted wrapper for money_in_words"""
    try:
        from frappe.utils import money_in_words
        return money_in_words(flt(amount), currency)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "FNF get_money_in_words")
        return ""
