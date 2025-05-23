# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname
from hrms.controllers.employee_boarding_controller import EmployeeBoardingController
from datetime import datetime, timedelta
from frappe.model.document import Document



class HoldSalaryEmployee(Document):
	def before_save(self):
		if self.salary_hold == 0 and self.salary_release == 0:
			frappe.throw(_("Can not be empty salary hold and salary release checkbox"))

		if self.salary_hold == 1:
			self.salary_release = 0
		elif self.salary_release == 1:
			self.salary_hold = 0
			
		if self.salary_release == 1 and self.last_working_day and not self.salary_release_date:
			self.salary_release_date = getdate(self.last_working_day) + timedelta(days=45)

		elif self.salary_release == 0:
			self.salary_release_date = None
