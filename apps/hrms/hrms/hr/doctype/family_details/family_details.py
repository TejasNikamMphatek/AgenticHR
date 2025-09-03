# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today

class FamilyDetails(Document):

    def before_save(self):
        current_date = getdate(today())
        for fp_val in self.family_data:
            try:
                if not fp_val.dob:
                    continue  
                
                fp_dob = getdate(fp_val.dob)
                fp_age = (
                    current_date.year - fp_dob.year -
                    ((current_date.month, current_date.day) < (fp_dob.month, fp_dob.day))
                )
                fp_val.age = fp_age  

            except ValueError as e:
                frappe.throw(f"Error: Age is not setting for family person {fp_val.name1}")

    def before_insert(self):
        # Check if Family Details already exists for this employee
        check_exist = frappe.db.exists("Family Details", {"employee": self.employee})

        if check_exist:
            frappe.throw(
                title="Duplicate Entry",
                msg=f"Record already exists for Employee {self.employee_name}"
            )
