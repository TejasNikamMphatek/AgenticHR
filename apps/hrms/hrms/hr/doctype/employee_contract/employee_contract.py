# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeContract(Document):
    def before_save(self):
        if self.contracts_information:
            seen = set()
            for contract_info in self.contracts_information:
                if contract_info.employee in seen:
                    frappe.throw(f"Contract already available for employee {contract_info.employee}.")
                seen.add(contract_info.employee)