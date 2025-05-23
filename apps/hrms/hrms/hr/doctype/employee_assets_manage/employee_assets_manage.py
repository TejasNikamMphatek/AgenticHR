# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from hrms.hr.utils import validate_active_employee
from frappe.utils import add_days, date_diff, format_date, get_link_to_form, getdate, get_fullname


class EmployeeAssetsManage(Document):
	# pass
	def validate(self):
		validate_active_employee(self.employee)
		
	
	def before_save(self):
		self.total_recover_amount = 0
		for assets in self.get("assets_details"):
			if assets.recieved_assets_return == 0:
				self.total_recover_amount += assets.assets_price * assets.asset_quantity
			
			if assets.recieved_assets_return == 1 and assets.assets_status == "Recover Amount":
				self.total_recover_amount += assets.assets_price * assets.asset_quantity
			
		
		if self.send_email == 1 and self.total_recover_amount > 0:
			self.notifyHR_Recovery()
		
		if self.send_email == 1 and self.total_recover_amount <= 0:
			frappe.msgprint(
					_("The total recover amount must be greater than 0 to send the email.")
			)

		
	def notifyHR_Recovery(self):
		hr_email = frappe.db.get_single_value("HR Settings", "hr_common_email")
		if not hr_email:
			frappe.msgprint(
				_("Please set default HR Common Email in HR Settings.")
			)
			return

		parent_doc = frappe.get_doc("Employee Assets Manage", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("Email Template Setting", "notify_hr_asset_recovery")
		if not template:
			frappe.msgprint(
				_("Please set default template for 'Notify HR Asset Recovery' Template in Email Template Setting.")
			)
			return

		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response_, args)
		self.notify(
			{
				"message_to": hr_email,
				"subject": email_template.subject,
				"message": message,
			}
		)
	
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
				)
				frappe.msgprint(_("Email sent to {0}").format(contact))
			except frappe.OutgoingEmailError:
				pass

			

			
			