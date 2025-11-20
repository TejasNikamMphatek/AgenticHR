import frappe
from frappe import _

@frappe.whitelist()
def get_permission_query_conditions(user=None):
    """Return condition to restrict Employee records based on user role."""
    if not user or user == "Administrator":
        return ""

    roles = set(frappe.get_roles(user))

    # HR and Onboarding roles can see all Employee records
    if {"HR Manager", "HR User", "Onboarding Employee"} & roles:
        return ""

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        # User not linked to any Employee record
        return "1 = 0"

    # Restrict visibility to only their own record
    return f"`tabEmployee`.name = {frappe.db.escape(employee)}"


@frappe.whitelist(allow_guest=False)
def has_permission(doc, user=None):
    """Check if the user has permission to access or create Employee records."""
    if not user or user == "Administrator":
        return True

    roles = set(frappe.get_roles(user))

    # Allow HR, Onboarding Employee to create/edit Employee records
    if {"HR Manager", "HR User", "Onboarding Employee"} & roles:
        return True

    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return False

    # Allow non-HR users only to access their own record
    return doc.name == employee
