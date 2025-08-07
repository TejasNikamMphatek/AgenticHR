# Copyright (c) 2018, Pipal ERP  and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname

from erpnext.setup.doctype.employee.employee import is_holiday

from hrms.hr.utils import validate_active_employee, validate_dates
from datetime import timedelta


class OverlappingAttendanceRequestError(frappe.ValidationError):
	pass


class AttendanceRequest(Document):
	def validate(self):
		self.validate_request_approver()
		validate_active_employee(self.employee)
		validate_dates(self, self.from_date, self.to_date)
		self.validate_half_day()
		self.validate_request_overlap()

	def validate_request_approver(self):
		if self.request_approver:
			req_approver_name = frappe.db.get_value(
				"Employee",
				{"user_id": self.request_approver, "status": "Active"},
				"employee_name"
			)
			self.request_approver_name = req_approver_name
		else:
			self.request_approver_name = ''

	def validate_half_day(self):
		if self.half_day:
			if not getdate(self.from_date) <= getdate(self.half_day_date) <= getdate(self.to_date):
				frappe.throw(_("Half day date should be in between from date and to date"))

	def validate_request_overlap(self):
		if not self.name:
			self.name = "New Attendance Request"

		Request = frappe.qb.DocType("Attendance Request")
		overlapping_request = (
			frappe.qb.from_(Request)
			.select(Request.name)
			.where(
				(Request.employee == self.employee)
				& (Request.docstatus < 2)
				& (Request.name != self.name)
				& (self.to_date >= Request.from_date)
				& (self.from_date <= Request.to_date)
			)
		).run(as_dict=True)

		if overlapping_request:
			self.throw_overlap_error(overlapping_request[0].name)

	def throw_overlap_error(self, overlapping_request: str):
		msg = _("Employee {0} already has an Attendance Request {1} that overlaps with this period").format(
			frappe.bold(self.employee),
			get_link_to_form("Attendance Request", overlapping_request),
		)

		frappe.throw(msg, title=_("Overlapping Attendance Request"), exc=OverlappingAttendanceRequestError)

	def on_submit(self):
		if self.status in ["Open",""]:
			frappe.throw(_("Only Attendance Req. with status 'Rejected' and 'Accepted' can be submitted"))
		
		self.notify_employee_att_status()
		if self.status in ["Accepted"]:
			self.create_attendance_records()

	def after_insert(self):
		self.notify_attendance_approver()

	def notify_attendance_approver(self):
		if self.request_approver:
			parent_doc = frappe.get_doc("Attendance Request", self.name)
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value("HR Settings", "attendance_request_template")
			if not template:
				frappe.msgprint(
					_("Please set default template for Attendance Request Template in HR Settings.")
				)
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response_, args)
			self.notify(
				{
					# for post in messages
					"message": message,
					"message_to": self.request_approver,
					# for email
					"subject": email_template.subject,
				}
			)
	
	def notify_employee_att_status(self):
		if self.employee:
			email_to = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
			parent_doc = frappe.get_doc("Attendance Request", self.name)
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value("HR Settings", "attendance_request_response_template")
			if not template:
				frappe.msgprint(
					_("Please set default template for Attendance Request Response Template in HR Settings.")
				)
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response_, args)
			self.notify(
				{
					# for post in messages
					"message": message,
					"message_to": email_to,
					# for email
					"subject": email_template.subject,
				}
			)
		
	def notify(self, args):
		args = frappe._dict(args)
		# print(args)
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

	def on_cancel(self):
		attendance_list = frappe.get_all(
			"Attendance", {"employee": self.employee, "attendance_request": self.name, "docstatus": 1}
		)
		if attendance_list:
			for attendance in attendance_list:
				attendance_obj = frappe.get_doc("Attendance", attendance["name"])
				attendance_obj.cancel()

	def create_attendance_records(self):
		request_days = date_diff(self.to_date, self.from_date) + 1
		for day in range(request_days):
			attendance_date = add_days(self.from_date, day)
			if self.should_mark_attendance(attendance_date):
				self.create_or_update_attendance(attendance_date)

	def create_or_update_attendance(self, date: str):
		attendance_name = self.get_attendance_record(date)
		status = self.get_attendance_status(date)

		if attendance_name:
			# update existing attendance, change the status
			doc = frappe.get_doc("Attendance", attendance_name)
			old_status = doc.status

			if old_status != status:
				doc.db_set({"status": status, "attendance_request": self.name})
				text = _("changed the status from {0} to {1} via Attendance Request").format(
					frappe.bold(old_status), frappe.bold(status)
				)
				doc.add_comment(comment_type="Info", text=text)

				frappe.msgprint(
					_("Updated status from {0} to {1} for date {2} in the attendance record {3}").format(
						frappe.bold(old_status),
						frappe.bold(status),
						frappe.bold(format_date(date)),
						get_link_to_form("Attendance", doc.name),
					),
					title=_("Attendance Updated"),
				)
		else:
			# submit a new attendance record
			doc = frappe.new_doc("Attendance")
			doc.employee = self.employee
			doc.attendance_date = date
			doc.shift = self.shift
			doc.company = self.company
			doc.attendance_request = self.name
			doc.status = status
			doc.insert(ignore_permissions=True)
			doc.submit()

	def should_mark_attendance(self, attendance_date: str) -> bool:
		# Check if attendance_date is a holiday
		if not self.include_holidays and is_holiday(self.employee, attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as it is a Holiday.").format(
					frappe.bold(format_date(attendance_date))
				)
			)
			return False

		# Check if employee is on leave
		if self.has_leave_record(attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as {1} is on leave.").format(
					frappe.bold(format_date(attendance_date)), frappe.bold(self.employee)
				)
			)
			return False

		return True

	def has_leave_record(self, attendance_date: str) -> str | None:
		return frappe.db.exists(
			"Leave Application",
			{
				"employee": self.employee,
				"docstatus": 1,
				"from_date": ("<=", attendance_date),
				"to_date": (">=", attendance_date),
			},
		)

	def get_attendance_record(self, attendance_date: str) -> str | None:
		return frappe.db.exists(
			"Attendance",
			{
				"employee": self.employee,
				"attendance_date": attendance_date,
				"docstatus": ("!=", 2),
			},
		)

	def get_attendance_status(self, attendance_date: str) -> str:
		if self.half_day and date_diff(getdate(self.half_day_date), getdate(attendance_date)) == 0:
			return "Half Day"
		elif self.reason == "Work From Home":
			return "Work From Home"
		else:
			return "Present"

	@frappe.whitelist()
	def get_attendance_warnings(self) -> list:
		attendance_warnings = []
		request_days = date_diff(self.to_date, self.from_date) + 1

		for day in range(request_days):
			attendance_date = add_days(self.from_date, day)

			if not self.include_holidays and is_holiday(self.employee, attendance_date):
				attendance_warnings.append({"date": attendance_date, "reason": "Holiday", "action": "Skip"})
			elif self.has_leave_record(attendance_date):
				attendance_warnings.append({"date": attendance_date, "reason": "On Leave", "action": "Skip"})
			else:
				attendance = self.get_attendance_record(attendance_date)
				if attendance:
					attendance_warnings.append(
						{
							"date": attendance_date,
							"reason": "Attendance already marked",
							"record": attendance,
							"action": "Overwrite",
						}
					)

		return attendance_warnings

@frappe.whitelist()
def get_missing_attendance_html(employee=None):
    if not employee:
        return "<div class='text-muted'>Please select an Employee.</div>"

    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "status": ["in", ["Absent", "Half Day"]]
        },
        fields=["attendance_date", "status"],
        order_by="attendance_date desc",
        limit_page_length=5
    )

    missing_entries = [
        {
            "date": getdate(att.attendance_date),
            "status": att.status
        }
        for att in attendance_records
    ]

    return frappe.render_template(
        "hrms/hr/doctype/attendance_request/missing_attendance.html",
        {"missing_entries": missing_entries}
    )
