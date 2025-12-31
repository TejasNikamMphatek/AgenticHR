from enum import Enum
import frappe


class OnboardingState(str, Enum):
    INIT = "INIT"
    USER_CREATED = "USER_CREATED"
    WAITING_FOR_EMPLOYEE_INPUT = "WAITING_FOR_EMPLOYEE_INPUT"
    HR_VALIDATION_PENDING = "HR_VALIDATION_PENDING"
    EMPLOYEE_CREATED = "EMPLOYEE_CREATED"
    ROLE_UPDATED = "ROLE_UPDATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

ALLOWED_TRANSITIONS = {
    OnboardingState.INIT: [
        OnboardingState.USER_CREATED,
        OnboardingState.HR_VALIDATION_PENDING,  # 🔑 REQUIRED
    ],
    OnboardingState.USER_CREATED: [
        OnboardingState.HR_VALIDATION_PENDING,
    ],
    OnboardingState.HR_VALIDATION_PENDING: [
        OnboardingState.EMPLOYEE_CREATED,
    ],
}



def validate_transition(current: OnboardingState, next_state: OnboardingState):
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if next_state not in allowed:
        frappe.throw(
            f"Invalid onboarding state transition: {current} → {next_state}"
        )


def get_state(key: str) -> OnboardingState:
    state = frappe.cache().get_value(f"hr_onboarding:{key}")
    return OnboardingState(state) if state else OnboardingState.INIT


def set_state(key: str, next_state: OnboardingState):
    current = get_state(key)
    validate_transition(current, next_state)
    frappe.cache().set_value(f"hr_onboarding:{key}", next_state.value)
