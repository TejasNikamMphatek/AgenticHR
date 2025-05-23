import frappe
from frappe.query_builder.functions import Count
from datetime import datetime, timedelta
@frappe.whitelist()
def getWhoIsInData():
	employee_checkin_statistics = get_employee_checkin_statistics()
	leave_applies = leave_applications()  # Call the corrected function
	return [
		{
            "checkin_statistics": employee_checkin_statistics,
            "leave_applies": leave_applies,
        }
    ]
import frappe

def get_employee_checkin_statistics():
    # Step 1: Get all active employees
    active_employees = frappe.get_all(
        "Employee",
        filters=[["status", "=", "Active"]],
        fields=[
            "employee_name",
            "name as emp_id",
            "designation",
            "reports_to",
            "default_shift",
        ]
    )
    
    total_employees = len(active_employees)

    # Step 2: Get today's check-ins
    today = frappe.utils.today()
    start_of_day = f"{today} 00:00:00"
    end_of_day = f"{today} 23:59:59"
    formatted_date = frappe.utils.format_date(today, "dd MMM yyyy")
    
    checkin_records = frappe.get_all(
        "Employee Checkin",
        filters=[
            ["log_type", "=", 'IN'],
            ["time", "between", [start_of_day, end_of_day]]
        ],
        fields=[
            "employee as emp_id",
            "time",  # Check-in time
            "shift_start",  # Retrieve shift start time from check-in records
            "shift_end"     # Retrieve shift end time from check-in records if needed
        ]
    )
    
    # Create a dictionary for fast lookup of check-ins
    checked_in_today = {checkin["emp_id"]: checkin for checkin in checkin_records}
    
    # Initialize counters and list for non-checking employees
    not_checked_in = 0
    late_checkins = 0
    on_time_checkins = 0
    late_checkin_employee = []
    not_checking_employees = []  # List to store names of employees who didn't check in

    # Step 3: Iterate over the active employees
    for employee in active_employees:
        emp_id = employee['emp_id']
        emp_name = employee['employee_name']
        emp_shift = employee['default_shift'] 
        
        if emp_id not in checked_in_today:
            not_checked_in += 1  # Employee did not check in today
            shift_info = frappe.get_all("Shift Type", filters=[["name", "=", emp_shift]], fields=["start_time", "end_time"])
            
            if shift_info:
                expected_checkin_time = shift_info[0]['start_time']
                shift_start = expected_checkin_time  # Set shift_start to expected_checkin_time
            else:
                expected_checkin_time = "Set Emp Shift"
                shift_start = None  # Explicitly set shift_start to None when no shift is found
            
            not_checking_employees.append({"employee_name": emp_name, "emp_id": emp_id, "expected_checkin_time": expected_checkin_time})  # Add to the list
        else:
            checkin_record = checked_in_today[emp_id]
            checkin_time = checkin_record['time']
            shift_start = checkin_record['shift_start']  # Get shift start from check-in record

            # Check if shift_start is not None before comparing
            if shift_start is not None and checkin_time > shift_start:
                late_checkins += 1
                late_checkin_employee.append({"employee_name": emp_name, **checkin_record})
            elif shift_start is not None:
                on_time_checkins += 1

    # Step 4: Calculate percentages safely
    not_checked_in_percentage = (not_checked_in / total_employees * 100) if total_employees else 0
    late_checkins_percentage = (late_checkins / total_employees * 100) if total_employees else 0
    on_time_checkins_percentage = (on_time_checkins / total_employees * 100) if total_employees else 0

    # Step 5: Return the results along with non-checking employees
    return {
        "total_employees": total_employees,
        "not_checked_in": not_checked_in,
        "not_checked_in_percentage": not_checked_in_percentage,
        "late_checkin_employee" : late_checkin_employee,
        "late_checkins": late_checkins,
        "late_checkins_percentage": late_checkins_percentage,
        "on_time_checkins": on_time_checkins,
        "on_time_checkins_percentage": on_time_checkins_percentage,
        "not_checking_employees": not_checking_employees,
        "data_date": formatted_date,
    }


def leave_applications():
    # Get today's date and the date for the next 15 days
    today = datetime.today().date()
    next_15_days = today + timedelta(days=15)

    
    leave_application = frappe.get_all(
        "Leave Application",
        filters=[
            ["status", "not in", ["Rejected", "Cancelled"]],
            ["from_date", "<=", next_15_days],  # Leave starts on or before the next 15 days
            ["to_date", ">=", today]  # Corrected operator here
        ],
        fields=[
            "employee as emp_id",
            "employee_name",
            "status",
            "from_date",
            "to_date",
            "total_leave_days",
            "leave_type",
            "leave_approver"
        ],
        order_by="posting_date"
    )
    total_leave_app = len(leave_application)
    # Step 1: Get the total count of active employees
    total_active_employees = frappe.get_all(
        "Employee",
        filters=[["status", "=", "Active"]],
        fields=["name as emp_id", "employee_name"]  # Corrected field alias
    )
    
    total_employees_count = len(total_active_employees)

    # Step 2: Calculate the percentage of employees who submitted leave applications
    employees_with_leave_applications = len(set(app["emp_id"] for app in leave_application))  # Unique employees who applied

    # Calculate overall leave application percentage
    leave_application_percent = (employees_with_leave_applications / total_employees_count * 100) if total_employees_count > 0 else 0

    # Step 3: Calculate leave applications specifically for today
    today_leave_application = frappe.get_all(
        "Leave Application",
        filters=[
            ["status", "not in", ["Rejected", "Cancelled"]],
            ["from_date", "<=", today],
            ["to_date", ">=", today]
        ],
        fields=["employee as emp_id"]
    )
    todays_ttl_leave_app = len(today_leave_application)
    employees_with_today_leave_applications = len(set(app["emp_id"] for app in today_leave_application))  # Unique employees who applied today

    # Calculate today's leave application percentage
    leave_application_percent_only_for_today = (employees_with_today_leave_applications / total_employees_count * 100) if total_employees_count > 0 else 0

    # Return a well-structured dictionary
    return {
        "leave_application": leave_application,
        "leave_application_percent": leave_application_percent,
        "leave_application_percent_only_for_today": leave_application_percent_only_for_today,
        "total_leave_app":total_leave_app,
        "todays_ttl_leave_app" : todays_ttl_leave_app,
    }
