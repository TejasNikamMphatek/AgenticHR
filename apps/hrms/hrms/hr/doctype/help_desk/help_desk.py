import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_fullname
from frappe.utils.file_manager import get_file

class HelpDesk(Document):
    def after_insert(self):
        self.notify_help_desk_user()

    def on_submit(self):
        if self.help_status in ["Assigned", "In Process", "Pending", "Cancelled",""]:
            frappe.throw(_("Only Help Applications with status 'Completed' and 'Rejected' can be submitted"))

        self.notify_help_desk_update()

        

    def notify_help_desk_update(self):
        if self.employee:
            email_to = self.employee_email
            parent_doc = frappe.get_doc("Help Desk", self.name)
            args = parent_doc.as_dict()

        template = frappe.db.get_single_value("Email Template Setting", "help_desk_update_to_final_status")
        if not template:
            frappe.msgprint(
                _("Please set default template for Help Desk Notify to HR in Email Template Setting.")
            )
            return
        
        email_template = frappe.get_doc("Email Template", template)
        message = frappe.render_template(email_template.response_, args)

        # Handling CC and BCC
        cc = [email.strip() for email in self.cc.split(',')] if self.cc else []
        bcc = [email.strip() for email in self.bcc.split(',')] if self.bcc else []

        self.notify({
            "message": message,
            "message_to": email_to,
            "subject": self.subject,
            "cc": cc,
            "bcc": bcc,
        })

   
    def notify_help_desk_user(self):
        if self.employee:
            email_to = self.default_email_to
            parent_doc = frappe.get_doc("Help Desk", self.name)
            args = parent_doc.as_dict()

        template = frappe.db.get_single_value("Email Template Setting", "help_desk_notify_to_hr")
        if not template:
            frappe.msgprint(
                _("Please set default template for Help Desk Notify to HR in Email Template Setting.")
            )
            return
        
        email_template = frappe.get_doc("Email Template", template)
        message = frappe.render_template(email_template.response_, args)

        # Handling CC and BCC
        cc = [email.strip() for email in self.cc.split(',')] if self.cc else []
        bcc = [email.strip() for email in self.bcc.split(',')] if self.bcc else []

        self.notify({
            "message": message,
            "message_to": email_to,
            "subject": self.subject,
            "cc": cc,
            "bcc": bcc,
        })

    def notify(self, args):
        args = frappe._dict(args)
        contact = args.message_to
        cc = args.get("cc", [])
        bcc = args.get("bcc", [])

        if not isinstance(contact, list):
            contact = frappe.get_doc("User", contact).email or contact

        sender = {
            "email": frappe.get_doc("User", frappe.session.user).email,
            "full_name": get_fullname(frappe.session.user)
        }

        try:
            frappe.sendmail(
                recipients=contact,
                sender=sender["email"],
                subject=args.subject,
                message=args.message,
                cc=cc,
                bcc=bcc,
            )
            frappe.msgprint(_("Email sent to {0}").format(contact))
        except frappe.OutgoingEmailError:
            frappe.msgprint(_("Failed to send email"))



