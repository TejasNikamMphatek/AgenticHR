# Copyright (c) 2018, Pipal ERP  and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.utils import today, add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname
from hrms.controllers.employee_boarding_controller import EmployeeBoardingController
from datetime import datetime, timedelta



class EmployeeSeparation(EmployeeBoardingController):
	
	def before_save(self):
		# self.lwd_as_per_policy = add_days(today(), self.notice_period)
		self.lwd_as_per_policy = add_days(self.submission_date, self.notice_period)

		if self.notice_period <= 0:
			frappe.throw(_("Please Set Notice Peroid in Employee Profile."))

		if self.final_decision_status in ['Exit Approved']: # here the issue is after save is not open to submit
			self.stop_sal_process_date()

		self.validate_resignation_form()


	def validate_resignation_form(self):
		if self.employee:
			existing_resignation = frappe.get_all(
				"Employee Separation",
				filters={"employee": self.employee, "docstatus": ["!=", 2], "name":["!=",self.name]},
				fields=["approved_lwd", "final_decision_status", "resign_status", "docstatus"],
				order_by="submission_date desc",
				limit=1
			)
			if existing_resignation:
				latest = existing_resignation[0]
				if latest['final_decision_status'] in ["In Process", "Exit Approved"]:
					frappe.throw(
								f"You have already submitted a resignation request."
								f"<br>Your current <b class='text-info'>Final Decision Status</b> is: <b>{latest['final_decision_status']}</b>."
							)




	def after_insert(self):
		self.notify_resign_from_employee()
	
	def on_submit(self):
		if self.resign_status in ["Pending", "In Process"]:
			frappe.throw(_("Only Employee Separation with status 'Completed' can be submitted"))
		elif self.final_decision_status in ["In Process"]:
			frappe.throw(_("Only Employee Separation with 'Final Decision Status' 'In Process' can not be submitted"))
		else :
			if self.stop_salary_process_date and self.final_decision_status == 'Exit Approved':
				self.insertHoldSalary()
				self.update_employee_relieving_date()
				frappe.msgprint(_("Employee Hold Salary created for this Employee."))
			self.notify_employee_for_resign_status()
			

	def on_cancel(self):
		hold_sal_emp = frappe.get_list(
			"Hold Salary Employee",
			filters={
				"employee": self.employee,
				"salary_hold_date": self.stop_salary_process_date,
				"salary_hold": 1
			},
			limit=1,
			order_by="creation desc"
		)
		if hold_sal_emp:
			hold_sal_emp_doc = frappe.get_doc("Hold Salary Employee", hold_sal_emp[0].name)
			hold_sal_emp_doc.delete(ignore_permissions=True)
		self.update_after_cancel_employee_relieving_date()
		

	def update_employee_relieving_date(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee.relieving_date = self.approved_lwd or self.lwd_as_per_policy
		employee.resignation_letter_date = self.submission_date
		employee.reason_for_leaving = f"Reason :{self.reason}  Description: {self.exit_reason_for_employee}"
		employee.save(ignore_permissions=True) 

	def update_after_cancel_employee_relieving_date(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee.relieving_date = None
		employee.resignation_letter_date = None
		employee.reason_for_leaving = None
		employee.save(ignore_permissions=True) 

	def insertHoldSalary(self):
		hold_sal_emp = frappe.get_doc({
				"doctype": "Hold Salary Employee",
				"employee": self.employee,
				"last_working_day": self.approved_lwd or self.lwd_as_per_policy,
				"salary_hold_date" : self.stop_salary_process_date,
				"salary_hold" : 1
			})
			
		hold_sal_emp.insert(ignore_permissions=True)


	def stop_sal_process_date(self):
		final_salary_date = (
			datetime.strptime(self.approved_lwd, "%Y-%m-%d") if self.approved_lwd else
			datetime.strptime(self.lwd_as_per_policy, "%Y-%m-%d")
		)
		month_start = final_salary_date.replace(day=1)
		days_from_month_start = (final_salary_date - month_start).days

		if days_from_month_start < 15 and (self.approved_lwd or self.lwd_as_per_policy):
			self.stop_salary_process_date = final_salary_date - timedelta(days=16)
		else:
			self.stop_salary_process_date = final_salary_date
		return

	def notify_resign_from_employee(self):
		if self.applying_to:
			# Fetch the Employee Separation document data
			parent_doc = frappe.get_doc("Employee Separation", self.name)
			args = parent_doc.as_dict()

			# Get the email template name from settings
			template = frappe.db.get_single_value("Email Template Setting", "employee_resign_notification")
			if not template:
				frappe.msgprint(
					_("Please set the default template for Employee Resign Notification in Email Template Settings.")
				)
				return

			email_template = frappe.get_doc("Email Template", template)

			# Get manager data
			manager_data = self.getEmployeeReportTo(self.applying_to)
			if not manager_data or not manager_data[0].get('user_id'):
				frappe.throw(_("No manager found for employee {}. Please check the applying_to field.").format(self.applying_to))

			# Add manager's name into args so it can be used in template
			args["applying_to_employee_name"] = manager_data[0].get("employee_name", "")

			# Prepare email details
			email_to = manager_data[0]['user_id']
			hr_email = frappe.db.get_single_value("HR Settings", "hr_common_email")
			if not hr_email:
				frappe.msgprint(
					_("Please set default HR Common Email in HR Settings.")
				)
				return
			
			cc = [hr_email]

			message = frappe.render_template(email_template.response_, args)

			# Send notification
			self.notify({
				"message_to": email_to,
				"cc": cc,
				"subject": email_template.subject,
				"message": message,
			})

	def notify_employee_for_resign_status(self):
		if self.employee:
			# Get employee email
			email_to = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
			if not email_to:
				frappe.throw(
					_("No email found for employee {}. Please check the employee UserId field.").format(self.employee)
				)

			# Base data from Employee Separation document
			parent_doc = frappe.get_doc("Employee Separation", self.name)
			args = parent_doc.as_dict()

			# Get manager details before rendering the template
			manager_data = self.getEmployeeReportTo(self.applying_to)
			if not manager_data or not manager_data[0].get('user_id'):
				frappe.throw(
					_("No manager found for employee {}. Please check the applying_to field.").format(self.applying_to)
				)

			manager_cc = manager_data[0]['user_id']
			args["applying_to_employee_name"] = manager_data[0].get("employee_name", "")

			# Get email template
			template = frappe.db.get_single_value("Email Template Setting", "resign_status_update_to_employee")
			if not template:
				frappe.msgprint(
					_("Please set default template for Resign Status Update to Employee Template in Employee Template Settings.")
				)
				return

			email_template = frappe.get_doc("Email Template", template)

			# Render template AFTER adding all required args
			message = frappe.render_template(email_template.response_, args)


			hr_email = frappe.db.get_single_value("HR Settings", "hr_common_email")
			if not hr_email:
				frappe.msgprint(
					_("Please set default HR Common Email in HR Settings.")
				)
				return
			

			# CC list
			cc = [hr_email, manager_cc]

			# Send notification
			self.notify({
				"message": message,
				"message_to": email_to,
				"cc": cc,
				"subject": email_template.subject,
			})
			
	def notify(self, args):
		args = frappe._dict(args)
		contact = args.message_to
		if not isinstance(contact, list):
			if not args.notify == "employee":
				contact = frappe.get_doc("User", contact).email or contact

			sender = dict()
			sender["email"] = frappe.get_doc("User", frappe.session.user).email
			sender["full_name"] = get_fullname(sender["email"])

			try:
				frappe.sendmail(
					recipients=contact,
					sender=sender["email"],
					subject=args.subject,
					message=args.message,
					cc=args.cc
				)
				frappe.msgprint(_("Email sent to {0}").format(contact))
			except frappe.OutgoingEmailError:
				pass
	
	@staticmethod
	def getEmployeeReportTo(applying_to):
		if applying_to:
			manager = frappe.get_all(
			"Employee",
			filters=[
				["status", "=", "active"],
				["employee", "=", applying_to]
			],
			fields=[
				"user_id",
				"company_email",
				"employee_name"
			],
			)
			return manager
		else:
			return []	