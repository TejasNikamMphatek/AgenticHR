import frappe
from frappe.query_builder.functions import Count
import unicodedata
from datetime import datetime, timedelta, date
import math
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from hrms.utils import get_employee_email

@frappe.whitelist()
def getConfirmationData():
	probation_employee = getProbationEmployee()
	confirmed_employee = getConfirmEmployee()
	return [
				{
					"probation_employee" : probation_employee,
					"confirmed_employee" : confirmed_employee,
				}
		   ]

def getProbationEmployee():
	thirty_days_from_now = datetime.today() + timedelta(days=30)
	# print(thirty_days_from_now)
	probation_employee =frappe.get_all(
		"Employee",
		filters = [
			["status", "=", "Active"],
			["confirmation_status","=","On Probation"],
			#["final_confirmation_date" ,"<", thirty_days_from_now]
			],
		fields=[
			"employee_name",
			"name as id",
			"date_of_joining",
			"final_confirmation_date",
			"confirmation_extend_date",
			"confirmation_extend_reason",
			"confirmation_status",
			"confirmation_status_feedback",
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
		conf_extend_date = employee.get('confirmation_extend_date')
		if final_confirmation_date:
			if conf_extend_date:
				confirmation_initiate_on_date = conf_extend_date - timedelta(days=7)
			else:
				confirmation_initiate_on_date = final_confirmation_date - timedelta(days=7)
			
			employee['confirmation_initiate_on_date'] = confirmation_initiate_on_date
		else:
			employee['confirmation_initiate_on_date'] = ""
	
	return probation_employee

def getConfirmEmployee():
	confirmed_employee =frappe.get_all(
		"Employee",
		filters = [
			["status", "=", "Active"],
			["confirmation_status","=","Confirmed"]
			],
		fields=[
			"employee_name",
			"name as id",
			"date_of_joining",
			"final_confirmation_date",
			"confirmation_extend_date",
			"confirmation_extend_reason",
			"confirmation_status",
			"confirmation_status_feedback",
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

	for employee in confirmed_employee:
		final_confirmation_date = employee.get('final_confirmation_date')
		reports_to = employee.get('reports_to')

		if final_confirmation_date:
			confirmation_initiate_on_date = final_confirmation_date - timedelta(days=7)
			employee['confirmation_initiate_on_date'] = confirmation_initiate_on_date
		else:
			employee['confirmation_initiate_on_date'] = ""

		if reports_to:
			reporting_manager_name =frappe.get_all(
				"Employee",
				filters = [
					["status", "=", "Active"],
					["name", "=", reports_to]
				],
				fields=[
					"employee_name as reports_to"
					],
				order_by="name"
				)

			if reporting_manager_name:
				employee['reports_to'] = reporting_manager_name[0]['reports_to']
			else:
				employee['reports_to'] = ""
		
	return confirmed_employee
