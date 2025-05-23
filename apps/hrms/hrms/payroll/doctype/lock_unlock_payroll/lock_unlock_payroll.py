# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname
from hrms.controllers.employee_boarding_controller import EmployeeBoardingController
from datetime import datetime, timedelta
from frappe.model.document import Document

class LockUnlockPayroll(Document):

	def before_save(self):
		payroll_start_date = getdate(self.payroll_start_date)
		payroll_end_date = getdate(self.payroll_end_date)

		months = [
			('apr', self.apr, self.apr_lock_date),
			('may', self.may, self.may_lock_date),
			('jun', self.jun, self.jun_lock_date),
			('jul', self.jul, self.jul_lock_date),
			('aug', self.aug, self.aug_lock_date),
			('sep', self.sep, self.sep_lock_date),
			('oct', self.oct, self.oct_lock_date),
			('nov', self.nov, self.nov_lock_date),
			('dec', self.dec, self.dec_lock_date),
			('jan', self.jan, self.jan_lock_date),
			('feb', self.feb, self.feb_lock_date),
			('mar', self.mar, self.mar_lock_date)
		]
		
		for index, value in enumerate(months, 0):
			month_name = value[0]
			month_flag = value[1]
			month_lock_date = value[2]

			if month_flag == 1:
				if month_lock_date is None:
					frappe.throw(_(f"Please Select {month_name.capitalize()} Lock Date"))
				else:
					lock_date_obj = getdate(month_lock_date)
					if lock_date_obj < payroll_start_date or lock_date_obj > payroll_end_date:
						frappe.throw(_('Select Date Between "Payroll Start Date" and "Payroll End Date"'))
					
					for m_index in range(index+1, len(months)):  # Start from the next month
						m_name, m_lock, m_lock_date = months[m_index]
					

						if m_lock_date:
							m_lock_date_obj = getdate(m_lock_date)  # Convert to date object
							if lock_date_obj >= m_lock_date_obj:
								frappe.throw(f"{m_name.capitalize()} lock date cannot be less than or equal to {month_name.capitalize()} date.")
					
		for lock_date in [
			self.jan_lock_date, self.feb_lock_date, self.mar_lock_date,
			self.apr_lock_date, self.may_lock_date, self.jun_lock_date,
			self.jul_lock_date, self.aug_lock_date, self.sep_lock_date,
			self.oct_lock_date, self.nov_lock_date, self.dec_lock_date
		]:
			if lock_date:
				lock_date_obj = getdate(lock_date)
				if not payroll_start_date <= lock_date_obj <= payroll_end_date:
					frappe.throw(_('Lock Date must be Between "Payroll Start Date" and "Payroll End Date"'))
				