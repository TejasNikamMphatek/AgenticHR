# Copyright (c) 2025,  Pipal ERP Pvt. Ltd. and contributors
# License: MIT. See LICENSE

from frappe.model.document import Document


class DataExport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		export_without_main_header: DF.Check
		file_type: DF.Literal["Excel", "CSV"]
		reference_doctype: DF.Literal["", "Employee", "Attendance", "Salary Slip", "Leave Application", "Attendance Request", "Employee Separation", "Employee Tax Exemption Declaration", "Employee Tax Exemption Proof Submission", "Hold Salary Employee", "Lock Unlock Payroll", "Payroll Entry", "Income Tax Slab", "Salary Structure", "Salary Structure Assignment", "Additional Salary"]
	# end: auto-generated types
	pass
