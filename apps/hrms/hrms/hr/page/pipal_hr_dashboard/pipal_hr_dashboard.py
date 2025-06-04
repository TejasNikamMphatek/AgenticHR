import frappe
from frappe.query_builder.functions import Count
import unicodedata
from datetime import datetime, timedelta ,date
import math
from dateutil.relativedelta import relativedelta
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname

@frappe.whitelist()
def getDashboardData():
	probation_employee = getProbationEmployee()
	resign_emp = getResignEmployee()
	attendance_req = getAttendanceReq()
	leave_application = getLeaveApplication()
	anni_emp = getAnniversaryEmployee()
	birthday_employee = getBirthdayEmployee()
	help_desk_request = getHelpDeskRequest()
	login_user = get_user()
	return [
				{
					"probation_employee" : probation_employee,
					"resign_emp" : resign_emp,
					"attendance_req" :attendance_req,
					"leave_application" : leave_application,
					"anni_emp" : anni_emp,
					"birthday_employee" : birthday_employee,
					"help_desk_request" : help_desk_request,
					"login_user" : login_user			}
		   ]



def getProbationEmployee():
	thirty_days_from_now = datetime.today() + timedelta(days=30)
	probation_employee =frappe.get_all(
		"Employee",
		filters = [
			["status", "=", "Active"],
			["confirmation_status","=","On Probation"],
			["final_confirmation_date" ,"<", thirty_days_from_now]
			],
		fields=[
			"employee_name",
			"name as id",
			"date_of_joining",
			"final_confirmation_date",
			"confirmation_status",
			"date_of_birth",
			"branch",
			"reports_to",
			"image",
			"department",
			"total_work_experience",
			"designation",
		],
		order_by="name",
	)
	for employee in probation_employee:
		final_confirmation_date = employee.get('final_confirmation_date')
		if final_confirmation_date:
			confirmation_initiate_on_date = final_confirmation_date - timedelta(days=7)
			employee['confirmation_initiate_on_date'] = confirmation_initiate_on_date
		else:
			employee['confirmation_initiate_on_date'] = ""
	
	return probation_employee


def getResignEmployee():
	resign_employee =frappe.get_all(
		"Employee Separation",
		filters = [
			["resign_status","!=","Completed"],
			],
		fields=[
			"employee_name",
			"name as id",
			"resign_status",
			"submission_date",
			"lwd_as_per_policy"
		],
		order_by="name",
	)
	return resign_employee

def getHelpDeskRequest():
	help_desk_request =frappe.get_all(
		"Help Desk",
		filters={
            # "help_status": ["not in", ["Completed", "Rejected"]],
			"docstatus": 0
        },
		fields=[
			"employee_name",
			"name as id",
			"help_status",
			"priority",
			"application_date"
		],
		order_by="application_date",
	)
	return help_desk_request


def getLeaveApplication():
	leave_application =frappe.get_all(
		"Leave Application",
		filters = [
			["docstatus","=", 0],
			],
		fields=[
			"employee_name",
			"name as id",
			"from_date",
			"to_date",
			"leave_approver",
			"leave_approver_name"
		],
		order_by="creation",
	)
	return leave_application

def getAttendanceReq():
	attendance_req =frappe.get_all(
		"Attendance Request",
		filters = [
			["docstatus","=", 0],
			["status", "=", "Open"],
			],
		fields=[
			"employee_name",
			"name as id",
			"from_date",
			"to_date"
		],
		order_by="creation",
	)
	return attendance_req

def getAnniversaryEmployee():
    today = datetime.today()
    today_month = today.month
    today_day = today.day

    # Adjust the query to work with MySQL using TIMESTAMPDIFF for year calculation
    query = """
        SELECT
            employee, employee_name, name as id, date_of_joining, image,user_id ,
            TIMESTAMPDIFF(YEAR, date_of_joining, CURDATE()) as employee_completed_year
        FROM
            `tabEmployee`
        WHERE
            status = 'Active'
            AND EXTRACT(MONTH FROM date_of_joining) = %s
            AND EXTRACT(DAY FROM date_of_joining) = %s
    """

    # Use frappe.db.sql for custom queries with parameters
    anni_employees = frappe.db.sql(query, (today_month, today_day), as_dict=True)

    return anni_employees

def getBirthdayEmployee():
    today = datetime.today()
    today_month = today.month
    today_day = today.day

    # Fetch only employees who are active and have their birthday today
    query = """
        SELECT
            employee, employee_name, name as id, date_of_birth, image, user_id
        FROM
            `tabEmployee`
        WHERE
            status = 'Active'
            AND EXTRACT(MONTH FROM date_of_birth) = %s
            AND EXTRACT(DAY FROM date_of_birth) = %s
    """

    # Use frappe.db.sql for custom queries with parameters
    birthday_employees = frappe.db.sql(query, (today_month, today_day), as_dict=True)

    return birthday_employees

@frappe.whitelist()
def sendAnniversaryWish(employee=None):
	anni_emp = getAnniversaryEmployee()
	if employee:
		wish_anni_emp = [emp for emp in anni_emp if emp.employee == employee]
		notify_to_anni_employee(wish_anni_emp)
	else:
		return [{status : "Not Sent" , error : "Employee Not Found"}]

def notify_to_anni_employee(wish_anni_emp = None):
	message = f"Happy Anniversary {wish_anni_emp[0]['employee_name']} you have completed {wish_anni_emp[0]['employee_completed_year']}"
	mail_to = wish_anni_emp[0]['user_id']
	notify(
		{
			# for post in messages
			"message": message,
			"message_to": mail_to,
			# for email
			"subject": "Anniversary Mail",
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

@frappe.whitelist()
def sendToAllAnniversaryWish():
	allAnniEmp = getAnniversaryEmployee()
	for emp in allAnniEmp:
		if(emp.employee_completed_year != 0):
			sendAnniversaryWish(emp.id)

@frappe.whitelist()
def sendBirthdayWish(employee = None):
	birth_emp = getBirthdayEmployee()
	if employee:
		wish_anni_emp = [emp for emp in birth_emp if emp.employee == employee]
		notify_to_birthday_employee(wish_anni_emp)
	else:
		return [{status : "Not Sent" , error : "Employee Not Found"}]

def notify_to_birthday_employee(birthday_emp = None):
	message = f"Wish you Happy Birthday {birthday_emp[0]['employee_name']}"
	mail_to = birthday_emp[0]['user_id']
	notify(
		{
			# for post in messages
			"message": message,
			"message_to": mail_to,
			# for email
			"subject": f"Happy Birthday {birthday_emp[0]['employee_name']} !",
		}
	)

@frappe.whitelist()
def sendToAllBirthdayWish():
	allBirthdayEmp = getBirthdayEmployee()
	for emp in allBirthdayEmp:
		sendBirthdayWish(emp.id)

@frappe.whitelist()
def sendEmailtoHelpDesk(data = None):
	return

def get_user():
	user = frappe.session.user
	login_user = frappe.get_all(
		"User",
		filters = [
			["enabled", "=", 1],
			["email", "=" , user]
			],
		fields=[
			"full_name",
			"role_profile_name",
			"birth_date",
			"user_image",
		],
		order_by="name",
	)
	return login_user