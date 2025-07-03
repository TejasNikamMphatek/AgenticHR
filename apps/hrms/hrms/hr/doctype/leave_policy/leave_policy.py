# Copyright (c) 2018, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class LeavePolicy(Document):
	def validate(self):
		if self.leave_policy_details:
			seen_leave_types = set()
			for lp_detail in self.leave_policy_details:
				# check duplicate leave types
				leave_types = lp_detail.leave_type
				if leave_types in seen_leave_types:
					frappe.throw(f"Duplicate leave type not allowed: {leave_types}")
				seen_leave_types.add(leave_types)
				#-------------------------------------------
				max_leaves_allowed = frappe.db.get_value(
					"Leave Type", lp_detail.leave_type, "max_leaves_allowed"
				)
				if max_leaves_allowed > 0 and lp_detail.annual_allocation > max_leaves_allowed:
					frappe.throw(
						_("Maximum leave allowed in the leave type {0} is {1}").format(
							lp_detail.leave_type, max_leaves_allowed
						)
					)
