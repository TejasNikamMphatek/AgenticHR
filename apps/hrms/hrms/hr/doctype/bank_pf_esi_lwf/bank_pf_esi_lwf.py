# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankPFESILWF(Document):
    def validate(self):
        if self.uan and not str(self.uan).isdigit():
            frappe.throw("UAN must contain numeric values only.")

        if self.esi_number and not str(self.esi_number).isdigit():
            frappe.throw("ESI Number must contain numeric values only.")
