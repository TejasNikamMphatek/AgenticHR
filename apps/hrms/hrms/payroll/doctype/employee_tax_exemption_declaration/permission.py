import frappe
from frappe import _


@frappe.whitelist()

def get_permission_query_conditions(user):
    if not user or user == "Administrator":
        return ""

    roles = frappe.get_roles(user)
    if "HR Manager" in roles or "HR User" in roles:
        return ""

    employee = frappe.db.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if not employee:
        return "1 = 0"

    return f"`tabEmployee Tax Exemption Declaration`.employee = '{employee.name}'"

@frappe.whitelist(allow_guest=False)
def has_permission(doc, user):
    if not user or user == "Administrator":
        return True

    roles = frappe.get_roles(user)
    if "HR Manager" in roles or "HR User" in roles:
        return True

    employee = frappe.db.get_value("Employee", {"user_id": user}, ["name"], as_dict=True)
    if not employee:
        return False

    return doc.employee == employee.name
