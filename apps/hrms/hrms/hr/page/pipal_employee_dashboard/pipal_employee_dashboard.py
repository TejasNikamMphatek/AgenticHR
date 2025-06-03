import frappe
from frappe.query_builder.functions import Count
import unicodedata
from datetime import datetime, timedelta ,date
import math
import frappe
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
import pytz
from datetime import datetime

@frappe.whitelist()


def getDashboardData():
	employee = get_employee()
	try:
		employee_shift = employee[0].default_shift
		employee_id = employee[0].id
		emp_holiday_list = employee[0].holiday_list

		shift_data = getShiftDetails(employee_shift)
		todaysSwipe = getTodaySwipe(employee_id,shift_data)
		valid_log_type = getTodayCheckin(employee_id,shift_data)
		payslip = getPayslip(employee_id)
		holiday_data = getUpcomingHoliday(emp_holiday_list)
		employee_declaration = getTaxExemptionDeclaration(employee_id)
		employee_tax_proof = getTaxProofSubmission(employee_id)
		
		return [
					{"employee" : employee},
					{"valid_log_type":valid_log_type},
					{"todaysSwipe" : todaysSwipe},
					{"payslip": payslip},
					{"holiday_data":holiday_data},
					{"employee_declaration": employee_declaration},
					{"employee_tax_proof": employee_tax_proof},
			]
	except IndexError:
		return[]
	except AttributeError:
		print("One of the attributes is missing.")
	except Exception as e:
		print(f"An unexpected error occurred: {e}")

def get_employee():
	user = frappe.session.user
	# user_role = frappe.get_roles(frappe.session.user)
	employees = frappe.get_all(
		"Employee",
		filters = [
			["status", "=", "Active"],
			["company_email", "=" , user]
			],
		fields=[
			"employee_name",
			"name as id",
			"holiday_list",
			"date_of_joining",
			"date_of_birth",
			"reports_to",
			"default_shift",
			"image",
			"designation",
		],
		order_by="name",
	)
	return employees

def getShiftDetails(employee_shift = None):
	response = frappe.get_all(
		"Shift Type",
		filters = [["name","=",employee_shift]],
		fields = [
            "name",
			"start_time",
			"end_time",
			"holiday_list",
			"begin_check_in_before_shift_start_time",
			"allow_check_out_after_shift_end_time"
		],
		limit = 1 
	)
	shift = response[0]
	adjusted_start_time = shift['start_time'] - timedelta(minutes=shift['begin_check_in_before_shift_start_time'])

	adjusted_end_time = shift['end_time'] + timedelta(minutes=shift['allow_check_out_after_shift_end_time'])

	today_date = datetime.now().date() 

	start_time = datetime.combine(today_date, datetime.min.time()) + shift['start_time']
	end_time = datetime.combine(today_date, datetime.min.time()) + shift['end_time']


	adjusted_start_time = datetime.combine(today_date, datetime.min.time()) + adjusted_start_time
	adjusted_end_time = datetime.combine(today_date, datetime.min.time()) + adjusted_end_time

	return {"actual_start_shift":adjusted_start_time,"actual_end_shift":adjusted_end_time}

def getTodayCheckin(employee_id,shift_data=None):
	checkin_record = frappe.get_all(
		"Employee Checkin",
		filters = [
			["employee", "=" ,employee_id],
			["time" , "between" , [shift_data['actual_start_shift'],shift_data['actual_end_shift']]]
		],
		fields = [
			"employee",
			"employee_name",
			"log_type",
			"time",
			"shift"
		],
		order_by = "time desc",
    	limit = 1
	)
	if checkin_record:
		validLog = validLogType(checkin_record[0])
	else:
		validLog = validLogType([])

	return validLog

def validLogType(checkin_record):
	if checkin_record:
		log_type = checkin_record['log_type']
		if log_type == "IN":
			log_type = "OUT"
		elif log_type == "OUT":
			log_type = "IN"
	else:
		log_type = "IN"

	return log_type

def getTodaySwipe(employee_id,shift_data=None):
	swipe_record_in = frappe.get_all(
		"Employee Checkin",
		filters = [
			["employee", "=" ,employee_id],
			["log_type", "=" ,'IN'],
			["time" , "between" , [shift_data['actual_start_shift'],shift_data['actual_end_shift']]]
		],
		fields = [
			"employee",
			"employee_name",
			"log_type",
			"time",
		],
		order_by = "time asc",
		limit = 1
	)
	swipe_record_out = frappe.get_all(
		"Employee Checkin",
		filters = [
			["employee", "=" ,employee_id],
			["log_type", "=" ,'OUT'],
			["time" , "between" , [shift_data['actual_start_shift'],shift_data['actual_end_shift']]]
		],
		fields = [
			"employee",
			"employee_name",
			"log_type",
			"time",
		],
		order_by = "time desc",
		limit = 1
	)	
	swipe_record = swipe_record_in + swipe_record_out
	# print(type(swipe_record))
	for record in swipe_record:
		if isinstance(record['time'], datetime):
			record['time'] = record['time'].strftime('%H:%M:%S')
		else:
			record['time'] = datetime.strptime(record['time'], '%Y-%m-%d %H:%M:%S.%f').strftime('%H:%M:%S')
	return swipe_record

def getPayslip(employee_id):
    payslip_record = frappe.get_all(
        "Salary Slip",
        filters=[
            ["employee", "=", employee_id],
            ["docstatus", "=", 1]
        ],
        fields=[
			"name",
			"company",
            "employee",
            "employee_name",
            "currency",
            "start_date",
            "gross_pay",
			"total_working_days",
            "payment_days",
            "total_deduction",
            "rounded_total as net_pay",
        ],
        order_by="start_date desc",
        limit=1
    )
    
    if payslip_record:
        payslip_record[0]['start_date'] = payslip_record[0]['start_date'].strftime('%b %Y')
        return payslip_record
    else:
        return [
			{
				"name":"",
				"company":"",
				"employee" : "",
				"employee_name" : "",
				"currency" : "",
				"start_date" : "",
				"gross_pay" : "",
				"total_working_days" : "",
				"payment_days" : "",
				"total_deduction" : "",
				"net_pay": "",
			}
		]

def getUpcomingHoliday(emp_holiday_list = None):
	today = datetime.today().date()
	# print(today)
	holiday_list = frappe.get_all(
		"Holiday",
		filters=[
			["weekly_off", "=", "0"],
			["parent", "=", emp_holiday_list],
			["holiday_date", ">=", today]
		],
		fields=[
			"description",
			"holiday_date",
		],
		order_by="holiday_date asc",
		limit=4
	)

	for holiday in holiday_list:
		formatted_date = holiday['holiday_date'].strftime('%d %b')
		formatted_day = holiday['holiday_date'].strftime('%A')
		
		holiday['holiday_date'] = formatted_date
		holiday['holiday_day'] = formatted_day

	return holiday_list

def getTaxExemptionDeclaration(emp_id = None):
	employee_declaration = frappe.get_all(
		"Employee Tax Exemption Declaration",
		filters =[
			["employee", "=", emp_id],
			["docstatus", "=", 1]
		],
		fields = [
			"employee",
			"employee_name",
			"currency",
			"payroll_period",
			"total_declared_amount",
			"total_exemption_amount"
		],
		order_by = "creation desc",
		limit = 1
	)
	# print("employee_declaration",employee_declaration)
	if employee_declaration:
		return employee_declaration
	else: 
		return[
			{
				"employee":"",
				"employee_name":"",
				"currency":"",
				"payroll_period":"",
				"total_declared_amount":"",
				"total_exemption_amount":"",
			}
		]

	
def getTaxProofSubmission(emp_id = None):
	employee_proof_submission = frappe.get_all(
		"Employee Tax Exemption Proof Submission",
		filters =[
			["employee", "=", emp_id],
			["docstatus", "=", 1]
		],
		fields = [
			"employee",
			"employee_name",
			"currency",
			"payroll_period",
			"total_actual_amount",
			"exemption_amount"
		],
		order_by = "creation desc",
		limit = 1
	)
	# print("employee_proof_submission",employee_proof_submission)
	if employee_proof_submission :
		return employee_proof_submission
	else:
		return [
			{
				"employee" : "",
				"employee_name" : "",
				"currency" : "",
				"payroll_period" : "",
				"total_actual_amount" : "",
				"exemption_amount" : "",
			}
		]

@frappe.whitelist()
def get_server_time():
	return {
        "server_time": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }
