import frappe
from frappe import _
from hrms.ai_agents.hr_onboarding_agent.state import (
    OnboardingState,
    get_state,
    set_state,
)



def ensure_doc_exists(doctype, name):
    """Create master data safely if missing"""
    if not frappe.db.exists(doctype, name):
        doc = frappe.new_doc(doctype)
        doc.name = name
        doc.insert(ignore_permissions=True)


def safe_get_user(user):
    if not frappe.db.exists("User", user):
        frappe.throw(f"User {user} does not exist")
    return frappe.get_doc("User", user)


# -----------------------------
# Helper: permission check
# -----------------------------
def _only_hr_or_admin():
    if not frappe.has_permission("User", "write"):
        frappe.throw(_("You do not have permission to perform this action"))


# -----------------------------
# Tool 1: check_user_exists
# -----------------------------
@frappe.whitelist()
def check_user_exists(email: str, employee_number: int | None = None):
    user = frappe.db.get_value("User", {"email": email}, "name")
    emp_no_user = None

    if employee_number:
        emp_no_user = frappe.db.get_value(
            "User",
            {"employee_number": employee_number},
            "name",
        )

    return {
        "exists": bool(user or emp_no_user),
        "user": user or emp_no_user,
    }


# -----------------------------
# Tool 2: create_user_tool
# -----------------------------
@frappe.whitelist()
def create_user_tool(data: dict):
    """
    Creates a User and assigns 'Onboarding Employee' role.
    Allowed only in INIT state.
    """
    _only_hr_or_admin()

    email = data.get("email")
    employee_number = data.get("employee_number")

    state_key = email
    current_state = get_state(state_key)

    if current_state != OnboardingState.INIT:
        return {
            "status": "ignored",
            "message": f"User already in onboarding flow ({current_state})",
        }

    # Idempotency
    if frappe.db.exists("User", {"email": email}):
        set_state(state_key, OnboardingState.USER_CREATED)
        return {
            "status": "exists",
            "user": email,
        }

    user = frappe.new_doc("User")
    user.update(
        {
            "email": email,
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "employee_number": employee_number,
            "mobile_no": data.get("mobile_no"),
            "enabled": 1,
        }
    )

    user.append_roles("Onboarding Employee")
    user.insert(ignore_permissions=True)

    set_state(state_key, OnboardingState.USER_CREATED)

    return {
        "status": "success",
        "user": user.name,
        "state": OnboardingState.USER_CREATED,
    }


# -----------------------------
# Tool 3: check_onboarding_completeness
# -----------------------------

@frappe.whitelist()
def check_onboarding_completeness(data):
    user = data.get("user")
    if not user:
        frappe.throw("user is required")

    user_doc = frappe.get_doc("User", user)

    missing = []
    if not user_doc.birth_date:
        missing.append("birth_date")
    if not user_doc.gender:
        missing.append("gender")

    if missing:
        return {
            "ready": False,
            "missing_fields": missing,
            "state": get_state(user),
        }

    # 🔑 AUTHORITATIVE STATE MOVE
    if get_state(user) != OnboardingState.HR_VALIDATION_PENDING:
        set_state(user, OnboardingState.HR_VALIDATION_PENDING)

    return {
        "ready": True,
        "missing_fields": [],
        "state": get_state(user),
    }

# -----------------------------
# Tool 4: create_employee_tool
# -----------------------------
import re
import frappe
from hrms.ai_agents.hr_onboarding_agent.state import (
    OnboardingState,
    get_state,
    set_state,
)


@frappe.whitelist()
def create_employee_tool(data):

    user = data["user"]
    employee_number = int(data["employee_number"])
    company = data["company"]
    date_of_joining = data["date_of_joining"]
    reports_to = data.get("reports_to")

    # -----------------------------
    # STATE GUARD
    # -----------------------------
    if get_state(user) != OnboardingState.HR_VALIDATION_PENDING:
        frappe.throw("Invalid onboarding state")

    # -----------------------------
    # LOAD USER
    # -----------------------------
    user_doc = frappe.get_doc("User", user)

    if not user_doc.birth_date or not user_doc.gender:
        frappe.throw("User profile incomplete")

    # -----------------------------
    # MOBILE (ERPNext SAFE)
    # -----------------------------
    raw_mobile = (user_doc.mobile_no or "").strip()
    digits = re.sub(r"\D", "", raw_mobile)

    if len(digits) == 10:
        mobile = "+91" + digits
    elif len(digits) == 12 and digits.startswith("91"):
        mobile = "+" + digits
    else:
        frappe.throw(
            f"Invalid mobile number for user {user}. "
            "Expected 10-digit number or +91XXXXXXXXXX format."
        )

    # -----------------------------
    # IDEMPOTENCY
    # -----------------------------
    # if frappe.db.exists("Employee", str(employee_number)):
    #     return {
    #         "status": "exists",
    #         "employee": str(employee_number),
    #         "state": OnboardingState.EMPLOYEE_CREATED,
    #     }
    # if frappe.db.exists("Employee", str(employee_number)):
    #     if get_state(user) != OnboardingState.EMPLOYEE_CREATED:
    #         set_state(user, OnboardingState.EMPLOYEE_CREATED)

    #     return {
    #     "status": "exists",
    #     "employee": str(employee_number),
    #     "state": OnboardingState.EMPLOYEE_CREATED,
    # }
    if frappe.db.exists("Employee", str(employee_number)):
        return {
        "status": "exists",
        "employee": str(employee_number),
        "state": get_state(user),
    }
    

    # -----------------------------
    # CREATE EMPLOYEE
    # -----------------------------
    emp = frappe.new_doc("Employee")

    emp.employee_number = employee_number
    emp.first_name = user_doc.first_name
    emp.middle_name = user_doc.middle_name
    emp.last_name = user_doc.last_name
    emp.employee_name = " ".join(
        filter(None, [emp.first_name, emp.middle_name, emp.last_name])
    )

    emp.company = company
    emp.status = "Active"
    emp.gender = user_doc.gender
    emp.date_of_birth = user_doc.birth_date
    emp.date_of_joining = date_of_joining
    emp.user_id = user

    if reports_to:
        emp.reports_to = reports_to

    # -----------------------------
    # 📞 PHONE (FIXED)
    # -----------------------------
    emp.cell_number = mobile
    emp.emergency_phone_number = mobile  # 🔥 CORRECT FIELD – FIXES ERROR

    # -----------------------------
    # 📧 EMAIL
    # -----------------------------
    emp.personal_email = user
    emp.company_email = user

    # -----------------------------
    # 🏠 ADDRESS
    # -----------------------------
    emp.current_address = "Pune, India"
    emp.permanent_address = "Pune, India"
    emp.person_to_be_contacted = "HR"
    emp.relation = "HR"

    # -----------------------------
    # 💳 BANK
    # -----------------------------
    emp.bank_name = "HDFC"
    emp.bank_ac_no = str(employee_number)
    emp.ifsc_code = "HDFC0001234"

    emp.marital_status = "single"

    # -----------------------------
    # 🪪 PAN
    # -----------------------------
    emp.pan_number = f"PAN{employee_number}"
    emp.append("identity_documents", {
        "document_type": "Pan Card",
        "document_number": emp.pan_number,
        "name_on_document": emp.employee_name,
    })

    # -----------------------------
    # INSERT (NAME CONTROLLED)
    # -----------------------------
    emp.insert(
        ignore_permissions=True,
        set_name=str(employee_number)
    )

   

    return {
        "status": "success",
        "employee": emp.name,
        "employee_number": employee_number,
        
    }

# Tool 5: finalize_employee_role
# -----------------------------
@frappe.whitelist()
def finalize_employee_role(user: str):
    """
    Switch role from Onboarding Employee → Employee.
    """
    _only_hr_or_admin()

    current_state = get_state(user)

    if current_state != OnboardingState.EMPLOYEE_CREATED:
        frappe.throw(
            _("Invalid state for role finalization: {0}").format(current_state)
        )

    user_doc = frappe.get_doc("User", user)
    roles = [r.role for r in user_doc.roles]

    if "Onboarding Employee" in roles:
        user_doc.remove_roles("Onboarding Employee")

    if "Employee" not in roles:
        user_doc.append_roles("Employee")

    user_doc.save(ignore_permissions=True)

    set_state(user, OnboardingState.COMPLETED)

    return {
        "status": "success",
        "state": OnboardingState.COMPLETED,
    }
