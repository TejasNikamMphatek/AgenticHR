# Copyright (c) 2025, Pipal ERP Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import json

from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	cint,
	cstr,
	format_date,
	get_datetime,
	get_link_to_form,
	getdate,
	nowdate,
	format_time
	get_first_day,
)

from hrms.hr.doctype.shift_assignment.shift_assignment import has_overlapping_timings
from hrms.hr.utils import (
	get_holiday_dates_for_employee,
	get_holidays_for_employee,
	validate_active_employee,
)
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

from datetime import datetime
from frappe.desk.reportview import get_filters_cond
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift


class DuplicateAttendanceError(frappe.ValidationError):
	pass


class OverlappingShiftAttendanceError(frappe.ValidationError):
	pass


class Attendance(Document):
	def validate(self):
		from erpnext.controllers.status_updater import validate_status

		validate_status(self.status, ["Present", "Absent", "On Leave", "Half Day"])
		validate_active_employee(self.employee)
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.validate_overlapping_shift_attendance()
		self.validate_employee_status()
		self.check_leave_record()
		
	def before_save(self):
		self.validate_holiday_date_attendance()

	def on_cancel(self):
		self.unlink_attendance_from_checkins()

	def validate_attendance_date(self):
		date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")

		# leaves can be marked for future dates
		if (
			self.status != "On Leave"
			and not self.leave_application
			and getdate(self.attendance_date) > getdate(nowdate())
		):
			frappe.throw(
				_("Attendance can not be marked for future dates: {0}").format(
					frappe.bold(format_date(self.attendance_date)),
				)
			)
		elif date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
			frappe.throw(
				_("Attendance date {0} can not be less than employee {1}'s joining date: {2}").format(
					frappe.bold(format_date(self.attendance_date)),
					frappe.bold(self.employee),
					frappe.bold(format_date(date_of_joining)),
				)
			)

	def validate_duplicate_record(self):
		duplicate = self.get_duplicate_attendance_record()

		if duplicate:
			frappe.throw(
				_("Attendance for employee {0} is already marked for the date {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(format_date(self.attendance_date)),
					get_link_to_form("Attendance", duplicate),
				),
				title=_("Duplicate Attendance"),
				exc=DuplicateAttendanceError,
			)

	def get_duplicate_attendance_record(self) -> str | None:
		Attendance = frappe.qb.DocType("Attendance")
		query = (
			frappe.qb.from_(Attendance)
			.select(Attendance.name)
			.where(
				(Attendance.employee == self.employee)
				& (Attendance.docstatus < 2)
				& (Attendance.attendance_date == self.attendance_date)
				& (Attendance.name != self.name)
			)
		)

		if self.shift:
			query = query.where(
				((Attendance.shift.isnull()) | (Attendance.shift == ""))
				| (
					((Attendance.shift.isnotnull()) | (Attendance.shift != ""))
					& (Attendance.shift == self.shift)
				)
			)

		duplicate = query.run(pluck=True)

		return duplicate[0] if duplicate else None

	def validate_overlapping_shift_attendance(self):
		attendance = self.get_overlapping_shift_attendance()

		if attendance:
			frappe.throw(
				_("Attendance for employee {0} is already marked for an overlapping shift {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(attendance.shift),
					get_link_to_form("Attendance", attendance.name),
				),
				title=_("Overlapping Shift Attendance"),
				exc=OverlappingShiftAttendanceError,
			)

	def get_overlapping_shift_attendance(self) -> dict:
		if not self.shift:
			return {}

		Attendance = frappe.qb.DocType("Attendance")
		same_date_attendance = (
			frappe.qb.from_(Attendance)
			.select(Attendance.name, Attendance.shift)
			.where(
				(Attendance.employee == self.employee)
				& (Attendance.docstatus < 2)
				& (Attendance.attendance_date == self.attendance_date)
				& (Attendance.shift != self.shift)
				& (Attendance.name != self.name)
			)
		).run(as_dict=True)

		if same_date_attendance and has_overlapping_timings(self.shift, same_date_attendance[0].shift):
			return same_date_attendance[0]
		return {}

	def validate_employee_status(self):
		if frappe.db.get_value("Employee", self.employee, "status") == "Inactive":
			frappe.throw(_("Cannot mark attendance for an Inactive employee {0}").format(self.employee))

	def check_leave_record(self):
		LeaveApplication = frappe.qb.DocType("Leave Application")
		leave_record = (
			frappe.qb.from_(LeaveApplication)
			.select(
				LeaveApplication.leave_type,
				LeaveApplication.half_day,
				LeaveApplication.half_day_date,
				LeaveApplication.name,
			)
			.where(
				(LeaveApplication.employee == self.employee)
				& (self.attendance_date >= LeaveApplication.from_date)
				& (self.attendance_date <= LeaveApplication.to_date)
				& (LeaveApplication.status == "Approved")
				& (LeaveApplication.docstatus == 1)
			)
		).run(as_dict=True)

		if leave_record:
			for d in leave_record:
				self.leave_type = d.leave_type
				self.leave_application = d.name
				if d.half_day_date == getdate(self.attendance_date):
					self.status = "Half Day"
					frappe.msgprint(
						_("Employee {0} on Half day on {1}").format(
							self.employee, format_date(self.attendance_date)
						)
					)
				else:
					self.status = "On Leave"
					frappe.msgprint(
						_("Employee {0} is on Leave on {1}").format(
							self.employee, format_date(self.attendance_date)
						)
					)

		if self.status in ("On Leave", "Half Day"):
			if not leave_record:
				frappe.msgprint(
					_("No leave record found for employee {0} on {1}").format(
						self.employee, format_date(self.attendance_date)
					),
					alert=1,
				)
		elif self.leave_type:
			self.leave_type = None
			self.leave_application = None

	def validate_employee(self):
		emp = frappe.db.sql(
			"select name from `tabEmployee` where name = %s and status = 'Active'", self.employee
		)
		if not emp:
			frappe.throw(_("Employee {0} is not active or does not exist").format(self.employee))

	def unlink_attendance_from_checkins(self):
		EmployeeCheckin = frappe.qb.DocType("Employee Checkin")
		linked_logs = (
			frappe.qb.from_(EmployeeCheckin)
			.select(EmployeeCheckin.name)
			.where(EmployeeCheckin.attendance == self.name)
			.for_update()
			.run(as_dict=True)
		)

		if linked_logs:
			(
				frappe.qb.update(EmployeeCheckin)
				.set("attendance", "")
				.where(EmployeeCheckin.attendance == self.name)
			).run()

			frappe.msgprint(
				msg=_("Unlinked Attendance record from Employee Checkins: {}").format(
					", ".join(get_link_to_form("Employee Checkin", log.name) for log in linked_logs)
				),
				title=_("Unlinked logs"),
				indicator="blue",
				is_minimizable=True,
				wide=True,
			)


	def validate_holiday_date_attendance(self):
		if not self.attendance_date or not self.employee or self.status not in ["Present", "Absent", "Half Day"]:
			return
		
		applicable_holiday_list = get_holiday_list_for_employee(self.employee)
		if not applicable_holiday_list:
			return

		
		from_date = self.attendance_date
		to_date = self.attendance_date

		holiday_list = frappe.db.sql(
			"""
			SELECT name, holiday_date, weekly_off, description
			FROM `tabHoliday`
			WHERE parent = %s AND holiday_date BETWEEN %s AND %s
			""",
			(applicable_holiday_list, from_date, to_date),
			as_dict=True
		)
		
		for holiday in holiday_list:
			
			holiday_date = getdate(holiday.holiday_date)
			attendance_date = getdate(self.attendance_date)
			if holiday_date == attendance_date:
				frappe.throw(
					_("Attendance date <b> {0} </b> is a holiday : <b> {1} </b>")
					.format(self.attendance_date, holiday.description or "Holiday")
				)



@frappe.whitelist()
def get_events(start, end, filters=None):
	from frappe.desk.reportview import get_filters_cond
	events = []

	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})
	roles = frappe.get_roles(frappe.session.user)

	if any(role in roles for role in ['HR Manager']):
		employee = ''

	if not employee:
		if len(filters) > 2:
			filters = json.loads(filters)
			for i, filter_item in enumerate(filters):
				try:
					docTypeIs = filter_item[0]
					column = filter_item[1]
					operator = filter_item[2]
					value = filter_item[3]

					if docTypeIs == "Attendance" and column == "employee" and value:
						employee = value

				except IndexError as e:
					frappe.msgprint(f"Error: Filter {i + 1} is incomplete: {filter_item}")
		else:
			frappe.msgprint("Invalid filter for Attendance Info. Employee Selection is Required.")
	
	if not employee:
		return events

	conditions = get_filters_cond("Attendance", filters, [])
	add_attendance(events, start, end, employee_id = employee, conditions=conditions)
	add_holidays(events, start, end, employee)
	return events

def add_attendance(events, start, end, employee_id=None, conditions=None ):
	query = """select name, attendance_date, status, employee_name ,employee
		from `tabAttendance` where employee = %(employee)s and
		attendance_date between %(from_date)s and %(to_date)s
		and docstatus < 2"""

	if conditions:
		query += conditions

	# for d in frappe.db.sql(query, {"from_date": start, "to_date": end , "employee":employee_id}, as_dict=True):
	# 	e = {
	# 		"name": d.name,
	# 		"doctype": "Attendance",
	# 		"start": d.attendance_date,
	# 		"end": d.attendance_date,
	# 		# "title": f"{d.employee_name}: {cstr(d.status)}",
	# 		"title": "A" if d.status== "Absent" else "P" if d.status == "Present" else "HD" if d.status== "Half Day" else d.status,
	# 		"status": d.status,
	# 		"docstatus": d.docstatus,
	# 	}
	# 	if e not in events:
	# 		events.append(e)

	for d in frappe.db.sql(query, {"from_date": start, "to_date": end , "employee":employee_id}, as_dict=True):
		status_map = {
			"Present": "P",
			"Absent": "A",
			"Half Day": "HD",
			"Work From Home": "WFH"
		}

		# Convert status dynamically
		short_status = status_map.get(d.status, d.status)  # Uses the mapped value, falls back to original

		e = {
			"name": d.name,
			"doctype": "Attendance",
			"start": d.attendance_date,
			"end": d.attendance_date,
			"title": short_status,  # Use the mapped short status
			"status": d.status,
			"docstatus": d.docstatus,
		}

		if e not in events:
			events.append(e)



def add_holidays(events, start, end, employee=None):
	holidays = get_holidays_for_employee(employee, start, end)
	if not holidays:
		return

	# for holiday in holidays:
	# 	events.append(
	# 		{
	# 			"doctype": "Holiday",
	# 			"start": holiday.holiday_date,
	# 			"end": holiday.holiday_date,
	# 			"title": _("Holiday") + ": " + cstr(holiday.description),
	# 			"name": holiday.name,
	# 			"allDay": 1,
	# 		}
	# 	)

	for holiday in holidays:
		title = "WO" if holiday.weekly_off == 1 else holiday.description
		# print(holiday)
		events.append(
			{
				"doctype": "Holiday",
				"start": holiday.holiday_date,
				"end": holiday.holiday_date,
				"title": title,
				"name": holiday.name,
				"allDay": 1,
			}
		)


def mark_attendance(
	employee,
	attendance_date,
	status,
	shift=None,
	leave_type=None,
	late_entry=False,
	early_exit=False,
):
	savepoint = "attendance_creation"

	try:
		frappe.db.savepoint(savepoint)
		attendance = frappe.new_doc("Attendance")
		attendance.update(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": attendance_date,
				"status": status,
				"shift": shift,
				"leave_type": leave_type,
				"late_entry": late_entry,
				"early_exit": early_exit,
			}
		)
		attendance.insert()
		attendance.submit()
	except (DuplicateAttendanceError, OverlappingShiftAttendanceError):
		frappe.db.rollback(save_point=savepoint)
		return

	return attendance.name


@frappe.whitelist()
def mark_bulk_attendance(data):
	import json

	if isinstance(data, str):
		data = json.loads(data)
	data = frappe._dict(data)
	if not data.unmarked_days:
		frappe.throw(_("Please select a date."))
		return

	for date in data.unmarked_days:
		doc_dict = {
			"doctype": "Attendance",
			"employee": data.employee,
			"attendance_date": get_datetime(date),
			"status": data.status,
		}
		attendance = frappe.get_doc(doc_dict).insert()
		attendance.submit()


@frappe.whitelist()
def get_unmarked_days(employee, from_date, to_date, exclude_holidays=0):
	joining_date, relieving_date = frappe.get_cached_value(
		"Employee", employee, ["date_of_joining", "relieving_date"]
	)

	from_date = max(getdate(from_date), joining_date or getdate(from_date))
	to_date = min(getdate(to_date), relieving_date or getdate(to_date))

	records = frappe.get_all(
		"Attendance",
		fields=["attendance_date", "employee"],
		filters=[
			["attendance_date", ">=", from_date],
			["attendance_date", "<=", to_date],
			["employee", "=", employee],
			["docstatus", "!=", 2],
		],
	)

	marked_days = [getdate(record.attendance_date) for record in records]

	if cint(exclude_holidays):
		holiday_dates = get_holiday_dates_for_employee(employee, from_date, to_date)
		holidays = [getdate(record) for record in holiday_dates]
		marked_days.extend(holidays)

	unmarked_days = []

	while from_date <= to_date:
		if from_date not in marked_days:
			unmarked_days.append(from_date)

		from_date = add_days(from_date, 1)

	return unmarked_days



@frappe.whitelist()
def get_attendance_summary_for_date(date=None, filters=None):
	
	user = frappe.session.user
	roles = frappe.get_roles(user)
	employee = frappe.db.get_value("Employee", {"user_id": user})

	if any(role in roles for role in ['Projects Manager', 'System Manager']):
		try:
			filters = json.loads(filters)
			for filter_item in filters:
				if (
					len(filter_item) == 4 and
					filter_item[0] == "Attendance" and
					filter_item[1] == "employee"
				):
					employee = filter_item[3]  # override employee from filter
		except Exception as e:
			frappe.msgprint(f"Error parsing filters: {e}")
			return

	date = getdate(date)
	checkins = frappe.get_all(
		"Employee Checkin",
		fields=["time", "log_type"],
		filters={
			"employee": employee,
			"time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
		},
		order_by="time asc"
	)

	swipes = [format_time(c.time) for c in checkins]
	sessions = []
	total_hours = 0

	for i in range(0, len(checkins) - 1, 2):
		in_time = checkins[i].time
		out_time = checkins[i + 1].time
		hours = (get_datetime(out_time) - get_datetime(in_time)).total_seconds() / 3600.0
		sessions.append({
			"in": format_time(in_time),
			"out": format_time(out_time),
			"hours": round(hours, 2)
		})
		total_hours += hours

	shift_info = get_employee_shift(employee, get_datetime(f"{date} 00:00:00")) or {}

	return {
		"date": date,
		"employee": employee,
		"swipes": swipes,
		"sessions": sessions,
		"total_swipes": len(swipes),
		"total_hours": round(total_hours, 2),
		"average_hours": round(total_hours / len(sessions), 2) if sessions else 0,
		"shift": {
			"type": shift_info.get("shift_type", "Not Assigned"),
			"timing": f"{shift_info.get('start_time')} - {shift_info.get('end_time')}"
				if shift_info.get("start_time") else "N/A"
		}
	}
