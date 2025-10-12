import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import getdate, nowdate, add_days

@frappe.whitelist()
def getConfirmationData():
    """
    Get confirmation data based on user role
    - HR Manager: Get all employees
    - Projects Manager: Get only reporting employees
    """
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    
    # Check if user has required roles
    if "HR Manager" in user_roles:
        user_role = "HR Manager"
        probation_employee = getProbationEmployee()
        confirmed_employee = getConfirmedEmployee()
    elif "Projects Manager" in user_roles:
        user_role = "Projects Manager"
        # Get employee ID for current user
        employee_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee_id:
            frappe.throw(_("No employee record found for current user"))
        
        probation_employee = getProbationEmployee(reports_to=employee_id)
        confirmed_employee = getConfirmedEmployee(reports_to=employee_id)
    else:
        frappe.throw(_("You do not have permission to access this page"))
    
    return [{
        "probation_employee": probation_employee,
        "confirmed_employee": confirmed_employee,
        "user_role": user_role
    }]


def getProbationEmployee(reports_to=None):
    """
    Get employees on probation
    Args:
        reports_to: Filter by reporting manager (for Projects Manager)
    """
    filters = [
        ["status", "=", "Active"],
        ["confirmation_status", "=", "On Probation"]
    ]
    
    # Add reporting manager filter for Projects Manager
    if reports_to:
        filters.append(["reports_to", "=", reports_to])
    
    probation_employees = frappe.get_all(
        "Employee",
        filters=filters,
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
        order_by="final_confirmation_date asc",
    )
    
    # Add computed fields
    for employee in probation_employees:
        final_confirmation_date = employee.get('final_confirmation_date')
        conf_extend_date = employee.get('confirmation_extend_date')
        
        if final_confirmation_date:
            if conf_extend_date:
                confirmation_initiate_on_date = add_days(conf_extend_date, -7)
            else:
                confirmation_initiate_on_date = add_days(final_confirmation_date, -7)
            
            employee['confirmation_initiate_on_date'] = confirmation_initiate_on_date
        else:
            employee['confirmation_initiate_on_date'] = None
        
        # Get reporting manager name
        if employee.get('reports_to'):
            manager_name = frappe.db.get_value("Employee", employee['reports_to'], "employee_name")
            employee['reports_to'] = manager_name
    
    return probation_employees


def getConfirmedEmployee(reports_to=None):
    """
    Get confirmed employees
    Args:
        reports_to: Filter by reporting manager (for Projects Manager)
    """
    filters = [
        ["status", "=", "Active"],
        ["confirmation_status", "=", "Confirmed"]
    ]
    
    # Add reporting manager filter for Projects Manager
    if reports_to:
        filters.append(["reports_to", "=", reports_to])
    
    confirmed_employees = frappe.get_all(
        "Employee",
        filters=filters,
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
        order_by="final_confirmation_date desc",
    )
    
    # Add computed fields
    for employee in confirmed_employees:
        final_confirmation_date = employee.get('final_confirmation_date')
        
        if final_confirmation_date:
            confirmation_initiate_on_date = add_days(final_confirmation_date, -7)
            employee['confirmation_initiate_on_date'] = confirmation_initiate_on_date
        else:
            employee['confirmation_initiate_on_date'] = None
        
        # Get reporting manager name
        if employee.get('reports_to'):
            manager_name = frappe.db.get_value("Employee", employee['reports_to'], "employee_name")
            employee['reports_to'] = manager_name
    
    return confirmed_employees


@frappe.whitelist()
def updateEmployeeConfirmation(employee_id, confirmation_status, confirmation_status_feedback=None, 
                               confirmation_extend_date=None, confirmation_extend_reason=None):
    """
    Update employee confirmation status
    Uses ignore_permissions=True to allow Projects Manager to update
    """
    try:
        # Validate user has permission
        user = frappe.session.user
        user_roles = frappe.get_roles(user)
        
        if "HR Manager" not in user_roles and "Projects Manager" not in user_roles:
            frappe.throw(_("You do not have permission to update employee confirmation"))
        
        # For Projects Manager, verify the employee reports to them
        if "Projects Manager" in user_roles and "HR Manager" not in user_roles:
            manager_employee_id = frappe.db.get_value("Employee", {"user_id": user}, "name")
            employee_reports_to = frappe.db.get_value("Employee", employee_id, "reports_to")
            
            if employee_reports_to != manager_employee_id:
                frappe.throw(_("You can only update confirmation for employees reporting to you"))
        
        # Get employee document
        employee_doc = frappe.get_doc("Employee", employee_id)
        
        # Update fields
        employee_doc.confirmation_status = confirmation_status
        
        if confirmation_status_feedback:
            employee_doc.confirmation_status_feedback = confirmation_status_feedback
        
        if confirmation_extend_date:
            employee_doc.confirmation_extend_date = confirmation_extend_date
        
        if confirmation_extend_reason:
            employee_doc.confirmation_extend_reason = confirmation_extend_reason
        
        # Save with ignore_permissions=True to allow Projects Manager to update
        employee_doc.save(ignore_permissions=True)
        
        # Send notification email
        send_confirmation_notification(employee_doc, confirmation_status)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Employee confirmation status updated successfully")
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Employee Confirmation Update Error"))
        return {
            "success": False,
            "message": str(e)
        }


def send_confirmation_notification(employee_doc, confirmation_status):
    """
    Send email notification to employee about confirmation status
    """
    try:
        employee_email = employee_doc.user_id or employee_doc.personal_email or employee_doc.company_email
        
        if not employee_email:
            return
        
        subject = ""
        message = ""
        
        if confirmation_status == "Confirmed":
            subject = _("Congratulations! Your Employment has been Confirmed")
            message = f"""
                <p>Dear {employee_doc.employee_name},</p>
                <p>We are pleased to inform you that your employment with the company has been confirmed.</p>
                <p><strong>Confirmation Date:</strong> {employee_doc.final_confirmation_date}</p>
                <p><strong>Feedback:</strong> {employee_doc.confirmation_status_feedback or 'N/A'}</p>
                <p>Congratulations on this milestone!</p>
                <br>
                <p>Best Regards,<br>HR Department</p>
            """
        elif confirmation_status == "On Probation":
            subject = _("Probation Period Extended")
            message = f"""
                <p>Dear {employee_doc.employee_name},</p>
                <p>Your probation period has been extended.</p>
                <p><strong>Extended Until:</strong> {employee_doc.confirmation_extend_date}</p>
                <p><strong>Reason:</strong> {employee_doc.confirmation_extend_reason or 'N/A'}</p>
                <p><strong>Feedback:</strong> {employee_doc.confirmation_status_feedback or 'N/A'}</p>
                <p>Please continue to work towards meeting the expected standards.</p>
                <br>
                <p>Best Regards,<br>HR Department</p>
            """
        elif confirmation_status == "Rejected":
            subject = _("Employment Status Update")
            message = f"""
                <p>Dear {employee_doc.employee_name},</p>
                <p>We regret to inform you that your employment confirmation has not been approved.</p>
                <p><strong>Feedback:</strong> {employee_doc.confirmation_status_feedback or 'N/A'}</p>
                <p>Please contact HR for further details.</p>
                <br>
                <p>Best Regards,<br>HR Department</p>
            """
        
        frappe.sendmail(
            recipients=[employee_email],
            subject=subject,
            message=message,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Confirmation Notification Email Error"))