import frappe
from frappe import _


@frappe.whitelist()
def get_permission_query_conditions(user=None):
    """Return condition to restrict Salary Slip visibility based on user role."""
    if not user or user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))
    if {"HR Manager", "HR User"} & roles:
        # HR roles can see all records
        return ""

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        # User not linked to any Employee record
        return "1 = 0"

    # ✅ Employee can see only their own submitted Salary Slips
    return (
        f"`tabSalary Slip`.employee = {frappe.db.escape(employee)} "
        f"AND `tabSalary Slip`.docstatus = 1"
    )


@frappe.whitelist(allow_guest=False)
def has_permission(doc, user=None):
    """Check if the user has permission to access the given Salary Slip."""
    if not user or user == "Administrator":
        return True

    roles = set(frappe.get_roles(user))
    if {"HR Manager", "HR User"} & roles:
        return True

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return False

    # ✅ Employee can access only their own Salary Slip if it's submitted
    if doc.employee == employee and doc.docstatus == 1:
        return True

    return False
