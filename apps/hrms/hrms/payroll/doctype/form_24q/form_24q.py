# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Form24Q(Document):
	pass

	def validate(self):
    	# List of child table fieldnames
		quarter_tables = [
			'1st_quarter_april_june',
			'2nd_quarter_july_sep',
			'3rd_quarter_oct_dec',
			'4th_quarter_jan_mar'
		]

		for table_fieldname in quarter_tables:
			for row in self.get(table_fieldname):
				if not row.year:
					frappe.throw(f"Year is mandatory in {frappe.bold(table_fieldname.replace('_', ' ').title())} table.")

