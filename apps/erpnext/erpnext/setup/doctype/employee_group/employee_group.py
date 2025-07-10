# Copyright (c) 2018, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document
import frappe
from frappe import _

class EmployeeGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext.setup.doctype.employee_group_table.employee_group_table import EmployeeGroupTable

		employee_group_name: DF.Data
		employee_list: DF.Table[EmployeeGroupTable]
	# end: auto-generated types
	

	def validate(self):
		self.validate_the_duplicate_employee()

	def validate_the_duplicate_employee(self):
		if self.employee_list:
			seen = set()
			for emp_row in self.employee_list:
				if emp_row.employee in seen:
					frappe.throw(_("Duplicate employee found: {0}").format(emp_row.employee))
				seen.add(emp_row.employee)
	pass
