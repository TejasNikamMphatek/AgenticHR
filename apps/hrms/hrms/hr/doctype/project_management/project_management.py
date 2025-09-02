# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectManagement(Document):
	def before_save(self):
		seen = set()
		for member in self.project_team:
			if member.employee in seen:
				frappe.throw(f"Duplicate Employee {member.employee} found in Project Team.")
			seen.add(member.employee)
