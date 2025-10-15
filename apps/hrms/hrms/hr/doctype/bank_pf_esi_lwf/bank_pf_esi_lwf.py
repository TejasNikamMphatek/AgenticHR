import re
import frappe
from frappe.model.document import Document
from frappe import _

class BankPFESILWF(Document):
    def validate(self):
        # ✅ UAN Validation
        if self.uan and not re.fullmatch(r"\d{12}", self.uan):
            frappe.throw(_("PF UAN must be exactly 12 digits and contain only numbers."))

        # ✅ Bank Account Number (fetched from employee)
        if self.bank_account_number and not re.fullmatch(r"\d+", self.bank_account_number):
            frappe.throw(_("Bank Account Number must contain only numbers."))

        # ✅ Bank Account No. (manual entry)
        if self.bank_account_no and not re.fullmatch(r"\d+", self.bank_account_no):
            frappe.throw(_("Bank Account No. must contain only numbers."))
