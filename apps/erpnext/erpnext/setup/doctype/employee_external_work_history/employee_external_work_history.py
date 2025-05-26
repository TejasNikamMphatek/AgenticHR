# Copyright (c) 2025,  Pipal ERP Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from frappe.model.document import Document


class EmployeeExternalWorkHistory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.SmallText | None
		attachment_of_document: DF.Attach | None
		company_name: DF.Data
		contact: DF.Data | None
		designation: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		salary: DF.Currency
		total_experience: DF.Data
	# end: auto-generated types

	pass
