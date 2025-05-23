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
def getEngageData():
	anni_emp = getAnniversaryEmployee()
	birthday_employee = getBirthdayEmployee()
	latest_joiners = getLatestJoinedEmployees()
	return [
				{
					"anni_emp" : anni_emp,
					"birth_emp" : birthday_employee,
					"latest_joiners" : latest_joiners,
                }
		   ]

def getAnniversaryEmployee():
    today = datetime.today()
    today_month = today.month

    # Query to get employees with anniversaries in the current month and who have completed at least one year
    query = """
        SELECT
            employee, employee_name, name as id, date_of_joining, image, user_id,
            TIMESTAMPDIFF(YEAR, date_of_joining, CURDATE()) as employee_completed_year,
            -- Calculate the anniversary date in the current year
            DATE(CONCAT(YEAR(CURDATE()), '-', EXTRACT(MONTH FROM date_of_joining), '-', EXTRACT(DAY FROM date_of_joining))) as anniversary_date
        FROM
            `tabEmployee`
        WHERE
            status = 'Active'
            AND EXTRACT(MONTH FROM date_of_joining) = %s
            AND TIMESTAMPDIFF(YEAR, date_of_joining, CURDATE()) > 0
    """

    # Use frappe.db.sql for custom queries with parameters
    anni_employees = frappe.db.sql(query, (today_month,), as_dict=True)

    # Process results to calculate days before or after the anniversary
    for employee in anni_employees:
        anniversary_date = employee['anniversary_date']
        
        if isinstance(anniversary_date, str):
            anniversary_date = datetime.strptime(anniversary_date, '%Y-%m-%d').date()

        if anniversary_date > today.date():
            after_days = (anniversary_date - today.date()).days
            employee['days_until_anniversary'] = f"{after_days} days after"
        elif anniversary_date < today.date():
            before_days = (today.date() - anniversary_date).days
            employee['days_until_anniversary'] = f"{before_days} days before"
        else:
            employee['days_until_anniversary'] = "Today"

    return anni_employees

def getBirthdayEmployee():
    today = datetime.today()
    today_month = today.month

    # Fetch only employees who are active and have their birthday in the current month
    query = """
        SELECT
            employee, employee_name, name as id, date_of_birth, image, user_id,
            -- Calculate the birthday date in the current year
            DATE(CONCAT(YEAR(CURDATE()), '-', EXTRACT(MONTH FROM date_of_birth), '-', EXTRACT(DAY FROM date_of_birth))) as birthday_date
        FROM
            `tabEmployee`
        WHERE
            status = 'Active'
            AND EXTRACT(MONTH FROM date_of_birth) = %s
    """

    # Use frappe.db.sql for custom queries with parameters
    birthday_employees = frappe.db.sql(query, (today_month,), as_dict=True)

    # Process results to calculate days before or after the birthday
    for employee in birthday_employees:
        birthday_date = employee['birthday_date']
        
        if isinstance(birthday_date, str):
            birthday_date = datetime.strptime(birthday_date, '%Y-%m-%d').date()

        if birthday_date > today.date():
            after_days = (birthday_date - today.date()).days
            employee['days_until_birthday'] = f"{after_days} days after"
        elif birthday_date < today.date():
            before_days = (today.date() - birthday_date).days
            employee['days_until_birthday'] = f"{before_days} days before"
        else:
            employee['days_until_birthday'] = "Today"

    return birthday_employees
def getLatestJoinedEmployees():
    today = datetime.today()
    last_week = today - timedelta(days=7)

    # Fetch employees who joined between today and one week ago
    query = """
        SELECT
            employee, employee_name, name as id, date_of_joining, image, user_id
        FROM
            `tabEmployee`
        WHERE
            status = 'Active'
            AND date_of_joining BETWEEN %s AND %s
    """

    # Use frappe.db.sql for custom queries with parameters
    latest_joiners = frappe.db.sql(query, (last_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')), as_dict=True)

    # Process each employee to calculate how many days ago they joined
    for employee in latest_joiners:
        date_of_joining = employee['date_of_joining']

        if isinstance(date_of_joining, str):
            date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()

        days_ago = (today.date() - date_of_joining).days

        if days_ago == 0:
            employee['days_since_joining'] = "Joined Today"
        else:
            employee['days_since_joining'] = f"Joined {days_ago} days ago"

    return latest_joiners


@frappe.whitelist()
def sendAnniversaryWish(employee=None):
	anni_emp = getAnniversaryEmployee()
	if employee:
		wish_anni_emp = [emp for emp in anni_emp if emp.employee == employee]
		notify_to_anni_employee(wish_anni_emp)
	else:
		return [{status : "Not Sent" , error : "Employee Not Found"}]
	print(wish_anni_emp)

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
		sendAnniversaryWish(emp.id)

@frappe.whitelist()
def sendBirthdayWish(employee = None):
	birth_emp = getBirthdayEmployee()
	if employee:
		wish_anni_emp = [emp for emp in birth_emp if emp.employee == employee]
		notify_to_birthday_employee(wish_anni_emp)
	else:
		return [{status : "Not Sent" , error : "Employee Not Found"}]
	print(birth_emp)

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
