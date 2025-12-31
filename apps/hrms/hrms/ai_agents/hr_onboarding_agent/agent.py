import frappe
from frappe import _

from hrms.ai_agents.hr_onboarding_agent.state import (
    OnboardingState,
    get_state,
    set_state,
)

from hrms.ai_agents.hr_onboarding_agent.tools import (
    create_user_tool,
    check_onboarding_completeness,
    create_employee_tool,
    finalize_employee_role,
)


# -------------------------------------------------
# Internal: resolve single state key
# -------------------------------------------------
def _get_state_key(payload: dict) -> str:
    """
    State key is ALWAYS user email.
    """
    if not payload:
        frappe.throw("Payload is required")

    if payload.get("email"):
        return payload["email"]

    if payload.get("user"):
        return payload["user"]

    frappe.throw("Cannot determine state key (email/user missing)")


# -------------------------------------------------
# Command registry (AUTHORITATIVE)
# -------------------------------------------------
COMMANDS = {
    "create_user_for_employee": {
        "allowed_states": [OnboardingState.INIT],
        "handler": create_user_tool,
    },

    "check_onboarding_status": {
        # Read-only / progressive
        "allowed_states": [
            OnboardingState.INIT,
            OnboardingState.USER_CREATED,
            OnboardingState.HR_VALIDATION_PENDING,
        ],
        "handler": check_onboarding_completeness,
    },

    "create_employee": {
        "allowed_states": [OnboardingState.HR_VALIDATION_PENDING],
        "handler": create_employee_tool,
    },

    "finalize_employee": {
        "allowed_states": [OnboardingState.EMPLOYEE_CREATED],
        "handler": finalize_employee_role,
    },
}


# -------------------------------------------------
# Agent entry point
# -------------------------------------------------
@frappe.whitelist()
def run_hr_onboarding_agent(command: str, payload: dict):
    """
    Deterministic HR onboarding agent.
    No AI. No guessing. Pure workflow enforcement.
    """

    if command not in COMMANDS:
        frappe.throw(_("Unknown command: {0}").format(command))

    command_meta = COMMANDS[command]

    # Resolve state key
    state_key = _get_state_key(payload)

    # Read current state
    current_state = get_state(state_key)

    # Validate allowed state
    if current_state not in command_meta["allowed_states"]:
        frappe.throw(
            _("Command '{0}' not allowed in state '{1}'").format(
                command, current_state
            )
        )

    # Execute tool
    result = command_meta["handler"](payload)
    

    # Unified response
    return {
        "command": command,
        "state": get_state(state_key),
        "result": result,
    }
