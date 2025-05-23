import frappe
import unicodedata
import time
from frappe.query_builder.functions import Count
from datetime import datetime, timedelta ,date
from frappe.utils.background_jobs import enqueue
from dateutil.relativedelta import relativedelta
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname
import frappe

@frappe.whitelist()
def getMassCommunicationData(start=0, company=None, department=None, employee=None, designation=None):
    # Retrieve filter values correctly
    company = frappe.form_dict.get("company", company)
    department = frappe.form_dict.get("department", department)
    employee = frappe.form_dict.get("employee", employee)
    designation = frappe.form_dict.get("designation", designation)

    frappe.logger().info(f"Filters Received - Company: {company}, Department: {department}, Employee: {employee}, Designation: {designation}" )

    active_employee = getActiveEmployee(company, department, employee, designation)
    return [{"active_employee": active_employee}]

def getActiveEmployee(company=None, department=None, employee=None, designation=None):
    filters = [["status", "=", "Active"], ["user_id", "!=", ""]]

    if company:
        filters.append(["company", "=", company])
    if department:
        filters.append(["department", "=", department])
    if employee:
        filters.append(["name", "=", employee])
    if designation:
        filters.append(["designation", "=", designation])

    frappe.logger().info(f"Filters Applied: {filters}")
	
    active_employee = frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "employee_name",
            "name as id",
            "date_of_joining",
            "branch",
            "reports_to",
            "image",
            "department",
            "designation",
            "user_id"
        ],
        order_by="name",
    )
    return active_employee


@frappe.whitelist()
def sendEmailToAll(company=None, department=None, employee=None, designation=None):
	company = frappe.form_dict.get("company", company)
	department = frappe.form_dict.get("department", department)
	employee = frappe.form_dict.get("employee", employee)
	designation = frappe.form_dict.get("designation", designation)
	
	frappe.logger().info(f"Filters Received - Company: {company}, Department: {department}, Employee: {employee}, Designation: {designation}" )
	
	act_emp = getActiveEmployee(company, department, employee, designation)

	mass_communication_with_employee(act_emp)

def mass_communication_with_employee(employees = None):
	for employee in employees:
		if employee['user_id']:
			email_to = employee['user_id']
			parent_doc = frappe.get_doc("Page", "mass-communication")
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value("Email Template Setting", "mass_communication")
			if not template:
				frappe.msgprint(
					_("Please set default template for Mass Communication Template in Email Template Setting.")
				)
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response_, args)
			notify(
				{
					# for post in messages
					"message_to": email_to,
					"message": message,
					"subject": email_template.subject,
				}
			)

def notify(args):
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
				)
				frappe.msgprint(_("Email sent to {0}").format(contact))
			except frappe.OutgoingEmailError:
				pass
