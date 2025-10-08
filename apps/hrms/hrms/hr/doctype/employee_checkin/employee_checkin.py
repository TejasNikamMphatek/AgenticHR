# Copyright (c) 2019, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from datetime import datetime, timedelta, time
from frappe.model.document import Document
from frappe.utils import cint, now_datetime , get_datetime, get_time, get_fullname


from hrms.hr.doctype.shift_assignment.shift_assignment import (
	get_actual_start_end_datetime_of_shift,
)
from hrms.hr.utils import validate_active_employee


class EmployeeCheckin(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_duplicate_log()
		self.fetch_shift()

	def validate_duplicate_log(self):
		doc = frappe.db.exists(
			"Employee Checkin",
			{
				"employee": self.employee,
				"time": self.time,
				"name": ("!=", self.name),
				"log_type": self.log_type,
			},
		)
		if doc:
			doc_link = frappe.get_desk_link("Employee Checkin", doc)
			frappe.throw(
				_("This employee already has a log with the same timestamp.{0}").format("<Br>" + doc_link)
			)

	def fetch_shift(self):
		shift_actual_timings = get_actual_start_end_datetime_of_shift(
			self.employee, get_datetime(self.time), True
		)
		if shift_actual_timings:
			if (
				shift_actual_timings.shift_type.determine_check_in_and_check_out
				== "Strictly based on Log Type in Employee Checkin"
				and not self.log_type
				and not self.skip_auto_attendance
			):
				frappe.throw(
					_("Log Type is required for check-ins falling in the shift: {0}.").format(
						shift_actual_timings.shift_type.name
					)
				)
			if not self.attendance:
				self.shift = shift_actual_timings.shift_type.name
				self.shift_actual_start = shift_actual_timings.actual_start
				self.shift_actual_end = shift_actual_timings.actual_end
				self.shift_start = shift_actual_timings.start_datetime
				self.shift_end = shift_actual_timings.end_datetime
		else:
			self.shift = None

	def before_save(self):
		current_time = now_datetime().replace(microsecond=0)
		self_time = get_datetime(self.time).replace(microsecond=0)

		if self_time > current_time:
			# print("self.time is greater than current_time")
			frappe.throw(_("Cannot create a log in the future. Please check the timestamp: {0}").format(self.time), title=_("Invalid Time"))

@frappe.whitelist()
def add_log_based_on_employee_field(
	employee_field_value,
	timestamp,
	device_id=None,
	log_type=None,
	skip_auto_attendance=0,
	employee_fieldname="attendance_device_id",
):
	"""Finds the relevant Employee using the employee field value and creates a Employee Checkin.

	:param employee_field_value: The value to look for in employee field.
	:param timestamp: The timestamp of the Log. Currently expected in the following format as string: '2019-05-08 10:48:08.000000'
	:param device_id: (optional)Location / Device ID. A short string is expected.
	:param log_type: (optional)Direction of the Punch if available (IN/OUT).
	:param skip_auto_attendance: (optional)Skip auto attendance field will be set for this log(0/1).
	:param employee_fieldname: (Default: attendance_device_id)Name of the field in Employee DocType based on which employee lookup will happen.
	"""

	if not employee_field_value or not timestamp:
		frappe.throw(_("'employee_field_value' and 'timestamp' are required."))

	employee = frappe.db.get_values(
		"Employee",
		{employee_fieldname: employee_field_value},
		["name", "employee_name", employee_fieldname],
		as_dict=True,
	)
	if employee:
		employee = employee[0]
	else:
		frappe.throw(
			_("No Employee found for the given employee field value. '{}': {}").format(
				employee_fieldname, employee_field_value
			)
		)

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee.name
	doc.employee_name = employee.employee_name
	doc.time = timestamp
	doc.device_id = device_id
	doc.log_type = log_type
	if cint(skip_auto_attendance) == 1:
		doc.skip_auto_attendance = "1"
	doc.insert()

	return doc


def mark_attendance_and_link_log(
	logs,
	attendance_status,
	attendance_date,
	working_hours=None,
	late_entry=False,
	early_exit=False,
	in_time=None,
	out_time=None,
	shift=None,
):
	"""Creates an attendance and links the attendance to the Employee Checkin.
	Note: If attendance is already present for the given date, the logs are marked as skipped and no exception is thrown.

	:param logs: The List of 'Employee Checkin'.
	:param attendance_status: Attendance status to be marked. One of: (Present, Absent, Half Day, Skip). Note: 'On Leave' is not supported by this function.
	:param attendance_date: Date of the attendance to be created.
	:param working_hours: (optional)Number of working hours for the given date.
	"""
	log_names = [x.name for x in logs]
	employee = logs[0].employee

	if attendance_status == "Skip":
		skip_attendance_in_checkins(log_names)
		return None

	elif attendance_status in ("Present", "Absent", "Half Day"):
		try:
			frappe.db.savepoint("attendance_creation")
			attendance = frappe.new_doc("Attendance")
			attendance.update(
				{
					"doctype": "Attendance",
					"employee": employee,
					"attendance_date": attendance_date,
					"status": attendance_status,
					"working_hours": working_hours,
					"shift": shift,
					"late_entry": late_entry,
					"early_exit": early_exit,
					"in_time": in_time,
					"out_time": out_time,
				}
			).submit()

			if attendance_status == "Absent":
				attendance.add_comment(
					text=_("Employee was marked Absent for not meeting the working hours threshold.")
				)

			update_attendance_in_checkins(log_names, attendance.name)
			return attendance

		except frappe.ValidationError as e:
			handle_attendance_exception(log_names, e)

	else:
		frappe.throw(_("{} is an invalid Attendance Status.").format(attendance_status))


def calculate_working_hours(logs, check_in_out_type, working_hours_calc_type):
	"""Given a set of logs in chronological order calculates the total working hours based on the parameters.
	Zero is returned for all invalid cases.

	:param logs: The List of 'Employee Checkin'.
	:param check_in_out_type: One of: 'Alternating entries as IN and OUT during the same shift', 'Strictly based on Log Type in Employee Checkin'
	:param working_hours_calc_type: One of: 'First Check-in and Last Check-out', 'Every Valid Check-in and Check-out'
	"""
	total_hours = 0
	in_time = out_time = None
	if check_in_out_type == "Alternating entries as IN and OUT during the same shift":
		in_time = logs[0].time
		if len(logs) >= 2:
			out_time = logs[-1].time
		if working_hours_calc_type == "First Check-in and Last Check-out":
			# assumption in this case: First log always taken as IN, Last log always taken as OUT
			total_hours = time_diff_in_hours(in_time, logs[-1].time)
		elif working_hours_calc_type == "Every Valid Check-in and Check-out":
			logs = logs[:]
			while len(logs) >= 2:
				total_hours += time_diff_in_hours(logs[0].time, logs[1].time)
				del logs[:2]

	elif check_in_out_type == "Strictly based on Log Type in Employee Checkin":
		if working_hours_calc_type == "First Check-in and Last Check-out":
			first_in_log_index = find_index_in_dict(logs, "log_type", "IN")
			first_in_log = logs[first_in_log_index] if first_in_log_index or first_in_log_index == 0 else None
			last_out_log_index = find_index_in_dict(reversed(logs), "log_type", "OUT")
			last_out_log = (
				logs[len(logs) - 1 - last_out_log_index]
				if last_out_log_index or last_out_log_index == 0
				else None
			)
			if first_in_log and last_out_log:
				in_time, out_time = first_in_log.time, last_out_log.time
				total_hours = time_diff_in_hours(in_time, out_time)
		elif working_hours_calc_type == "Every Valid Check-in and Check-out":
			in_log = out_log = None
			for log in logs:
				if in_log and out_log:
					if not in_time:
						in_time = in_log.time
					out_time = out_log.time
					total_hours += time_diff_in_hours(in_log.time, out_log.time)
					in_log = out_log = None
				if not in_log:
					in_log = log if log.log_type == "IN" else None
					if in_log and not in_time:
						in_time = in_log.time
				elif not out_log:
					out_log = log if log.log_type == "OUT" else None

			if in_log and out_log:
				out_time = out_log.time
				total_hours += time_diff_in_hours(in_log.time, out_log.time)

	return total_hours, in_time, out_time


def time_diff_in_hours(start, end):
	return round(float((end - start).total_seconds()) / 3600, 2)


def find_index_in_dict(dict_list, key, value):
	return next((index for (index, d) in enumerate(dict_list) if d[key] == value), None)


def handle_attendance_exception(log_names: list, error_message: str):
	frappe.db.rollback(save_point="attendance_creation")
	frappe.clear_messages()
	skip_attendance_in_checkins(log_names)
	add_comment_in_checkins(log_names, error_message)


def add_comment_in_checkins(log_names: list, error_message: str):
	text = "{prefix}<br>{error_message}".format(
		prefix=frappe.bold(_("Reason for skipping auto attendance:")), error_message=error_message
	)

	for name in log_names:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "Employee Checkin",
				"reference_name": name,
				"content": text,
			}
		).insert(ignore_permissions=True)


def skip_attendance_in_checkins(log_names: list):
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("skip_auto_attendance", 1)
		.where(EmployeeCheckin.name.isin(log_names))
	).run()


def update_attendance_in_checkins(log_names: list, attendance_id: str):
	EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
	(
		frappe.qb.update(EmployeeCheckin)
		.set("attendance", attendance_id)
		.where(EmployeeCheckin.name.isin(log_names))
	).run()


@frappe.whitelist()
def scheduled_notify_general_shift():
    try:
        return notify_employee_if_not_sign_in("General Shift")
    except Exception as e:
        frappe.log_error(message=str(e), title="Scheduled Notify Employee Error")
        return
@frappe.whitelist()
def notify_employee_if_not_sign_in(shift_name):
    try:
        # Get all related data
        shift_details = get_shift_details(shift_name)
        if not shift_details:
            frappe.log_error(
                message=f"Shift details not found for: {shift_name}",
                title="Shift Not Found - Check-in Notification"
            )
            frappe.db.commit()
            return {"status": "error", "message": "Shift not found"}

        shift_assignments = get_shift_assignments(shift_details)
        checked_in_employees = get_checkin_employees(shift_details)
        leave_applications = get_leave_applications()
        all_employees = get_active_employees(shift_details)

        # Calculate employees not checked in
        employees_not_checked_in = {emp["employee_number"] for emp in all_employees}

        if shift_assignments:
            employees_not_checked_in.update({sa["employee"] for sa in shift_assignments})

        if checked_in_employees:
            employees_not_checked_in.difference_update({c["employee"] for c in checked_in_employees})

        if leave_applications and "leave_applications" in leave_applications:
            leave_emps = {l["employee"] for l in leave_applications["leave_applications"]}
            employees_not_checked_in.difference_update(leave_emps)

        employees_not_checked_in = sorted(employees_not_checked_in)
        
        if not employees_not_checked_in:
            return {"status": "success", "message": "No employees to notify", "count": 0}

        employee_details = get_employee_details_by_ids(employees_not_checked_in)
        
        # Get email template
        template_name = frappe.db.get_single_value("HR Settings", "employee_checkin_notification")
        if not template_name:
            frappe.log_error(
                message="Email template not configured in HR Settings for 'employee_checkin_notification'",
                title="Missing Email Template - Check-in Notification"
            )
            frappe.db.commit()
            return {"status": "error", "message": "Email template not configured"}
        
        try:
            email_template = frappe.get_doc("Email Template", template_name)
        except Exception as e:
            frappe.log_error(
                message=f"Failed to fetch email template '{template_name}': {str(e)}",
                title="Email Template Error - Check-in Notification"
            )
            frappe.db.commit()
            return {"status": "error", "message": "Email template fetch failed"}
        
        # Send notifications
        success_count = 0
        failed_count = 0
        
        for employee in employee_details:
            if not employee.get('user_id'):
                continue
                
            try:
                args = {
                    "employee_number": employee.get('name'),
                    "employee_name": employee.get('employee_name'),
                    "date": datetime.today().strftime("%Y-%m-%d")
                }
                
                message = frappe.render_template(email_template.response_, args)
                
                # Send email notification
                email_sent = send_notification_email(
                    recipient=employee.get('user_id'),
                    subject=email_template.subject,
                    message=message,
                    employee_name=employee.get('employee_name'),
                    employee_number=employee.get('name')
                )
                
                if email_sent:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                frappe.log_error(
                    message=f"Failed to process notification for employee {employee.get('name')}: {str(e)}",
                    title="Employee Notification Processing Error"
                )
                continue
        
        frappe.db.commit()
        
        return {
            "status": "completed",
            "total": len(employee_details),
            "success": success_count,
            "failed": failed_count
        }
        
    except Exception as e:
        frappe.log_error(
            message=f"Critical error in notify_employee_if_not_sign_in for shift '{shift_name}': {str(e)}",
            title="Critical Error - Check-in Notification"
        )
        frappe.db.commit()
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_shift_details(shift_type=None):
    """Get shift details with calculated actual start and end times for today"""
    if not shift_type:
        return {}
    
    try:
        shift = frappe.db.get_value(
            "Shift Type",
            shift_type,
            [
                "name",
                "start_time",
                "end_time",
                "begin_check_in_before_shift_start_time",
                "allow_check_out_after_shift_end_time"
            ],
            as_dict=True
        )

        if not shift:
            return {}

        today = datetime.today().date()
        
        start_time_obj = get_time(shift.start_time)
        end_time_obj = get_time(shift.end_time)
        
        start_time = datetime.combine(today, start_time_obj)
        end_time = datetime.combine(today, end_time_obj)
        
        # Handle shifts that cross midnight
        if end_time <= start_time:
            end_time += timedelta(days=1)
        
        # Calculate actual times with grace periods
        actual_start_time = start_time - timedelta(
            minutes=shift.begin_check_in_before_shift_start_time or 0
        )
        actual_end_time = end_time + timedelta(
            minutes=shift.allow_check_out_after_shift_end_time or 0
        )
        
        return {
            "name": shift.name,
            "shift": shift.name,
            "actual_start_time": actual_start_time,
            "actual_end_time": actual_end_time
        }
    
    except Exception as e:
        frappe.log_error(
            message=f"Error processing shift details for {shift_type}: {str(e)}",
            title="Shift Details Processing Error"
        )
        return {}


@frappe.whitelist()
def get_leave_applications():
    """Get approved leave applications for today"""
    try:
        today = datetime.today().date()

        leave_applications = frappe.db.get_all(
            "Leave Application",
            filters={
                "from_date": ["<=", today],
                "to_date": [">=", today],
                "status": "Approved"
            },
            fields=["employee", "from_date", "to_date"]
        )

        for app in leave_applications:
            app["company_email"] = frappe.db.get_value("Employee", app["employee"], "company_email")

        return {"leave_applications": leave_applications} if leave_applications else {}
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching leave applications: {str(e)}",
            title="Leave Applications Fetch Error"
        )
        return {}


@frappe.whitelist()
def get_shift_assignments(shift_details):
    """Get active shift assignments for today"""
    if not shift_details or not shift_details.get('shift'):
        return []
    
    try:
        today = datetime.today().date()
        
        shift_assignments = frappe.db.get_all(
            "Shift Assignment",
            filters={
                "shift_type": shift_details['shift'],
                "start_date": ["<=", today],
                "end_date": [">=", today],
                "status": "Active",
            },
            fields=["employee", "employee_name"]
        )
        
        return shift_assignments
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching shift assignments for {shift_details.get('shift')}: {str(e)}",
            title="Shift Assignments Fetch Error"
        )
        return []


@frappe.whitelist()
def get_checkin_employees(shift_details):
    """Get employees who have checked in for the shift"""
    try:
        shift = shift_details['shift']
        start_time = get_datetime(shift_details['actual_start_time'])
        end_time = get_datetime(shift_details['actual_end_time'])

        employees = frappe.db.get_all(
            "Employee Checkin",
            filters=[
                ["log_type", "=", "IN"],
                ["shift", "=", shift],
                ["time", ">=", start_time],
                ["time", "<=", end_time],
            ],
            fields=["employee", "log_type", "time"],
            order_by="time asc"
        )

        return employees
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching checked-in employees for shift {shift_details.get('shift')}: {str(e)}",
            title="Check-in Employees Fetch Error"
        )
        return []


@frappe.whitelist()
def get_employee_details_by_ids(employee_ids):
    """Get employee details for specific employee IDs"""
    if not employee_ids:
        return []
    
    try:
        employees = frappe.db.get_all(
            "Employee",
            filters={
                "name": ["in", employee_ids],
                "status": "Active",
            },
            fields=["name", "employee_name", "user_id", "company_email"]
        )
        
        return employees
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching employee details: {str(e)}",
            title="Employee Details Fetch Error"
        )
        return []


@frappe.whitelist()
def get_active_employees(shift_details):
    """Get active employees assigned to the shift"""
    try:
        shift_name = shift_details['shift']
        employees = frappe.db.get_all(
            "Employee",
            filters=[
                ["status", "=", "Active"],
                ["default_shift", "=", shift_name],
                ["user_id", "is", "set"]
            ],
            fields=["name", "employee_number"]
        )
        return employees
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching active employees for shift {shift_details.get('shift')}: {str(e)}",
            title="Active Employees Fetch Error"
        )
        return []


def send_notification_email(recipient, subject, message, employee_name, employee_number):
    """
    Send email notification with error handling.
    Returns True if sent successfully, False otherwise.
    """
    try:
        # Try to send immediately
        frappe.sendmail(
            recipients=recipient,
            subject=subject,
            message=message,
            now=True
        )
        return True
        
    except frappe.OutgoingEmailError as e:
        # If immediate sending fails, try queuing
        try:
            frappe.sendmail(
                recipients=recipient,
                subject=subject,
                message=message,
                now=False  # Queue for later
            )
            frappe.log_error(
                message=f"Email queued (immediate send failed) for employee {employee_number} ({employee_name}) at {recipient}. Error: {str(e)}",
                title="Email Queued - Check-in Notification"
            )
            return True
        except Exception as queue_error:
            frappe.log_error(
                message=f"Failed to send/queue email for employee {employee_number} ({employee_name}) at {recipient}. Error: {str(queue_error)}",
                title="Email Send Failed - Check-in Notification"
            )
            return False
            
    except Exception as e:
        frappe.log_error(
            message=f"Unexpected error sending email to employee {employee_number} ({employee_name}) at {recipient}. Error: {str(e)}",
            title="Email Send Error - Check-in Notification"
        )
        return False
