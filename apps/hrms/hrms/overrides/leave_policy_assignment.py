# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, bold
from frappe.utils import add_days, date_diff, formatdate, rounded, getdate, today

from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import LeavePolicyAssignment
from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import LeaveLedgerEntry

@frappe.whitelist()
def get_overlapping_assignments(employee=None, effective_from=None, effective_to=None, leave_policy=None, current_doc_name=None):
    try:
        if not all([employee, effective_from, effective_to, leave_policy]):
            return {"success": False, "message": "Missing required fields: employee, effective_from, effective_to, leave_policy"}

        filters = {
            "employee": employee,
            "docstatus": 1,
            "effective_from": ["<=", effective_to],
            "effective_to": [">=", effective_from],
        }
        if current_doc_name:
            filters["name"] = ["!=", current_doc_name]

        assignments = frappe.get_list(
            "Leave Policy Assignment",
            filters=filters,
            fields=["name", "effective_from", "effective_to", "leave_policy"]
        )

        return {"success": True, "assignments": assignments}
    except Exception as e:
        frappe.log_error(f"Error in get_overlapping_assignments: {str(e)}", title="Debug: Get Overlap Error")
        return {"success": False, "message": f"Server error: {str(e)}"}

@frappe.whitelist()
def handle_leave_policy_override(employee=None, effective_from=None, effective_to=None, current_doc_name=None, leave_policy=None):
    try:
        frappe.log_error(
            message=f"handle_leave_policy_override: employee={employee}, effective_from={effective_from}, effective_to={effective_to}, current_doc_name={current_doc_name}, leave_policy={leave_policy}, user={frappe.session.user}",
            title="Debug: Handle Override Start"
        )

        if not frappe.session.user or frappe.session.user == "Guest":
            error_msg = "Invalid session: User not logged in or session expired"
            frappe.log_error(message=error_msg, title="Debug: Handle Override Session Error")
            return {"success": False, "message": error_msg}

        if not all([employee, effective_from, effective_to, leave_policy]):
            missing_fields = [f for f in ["employee", "effective_from", "effective_to", "leave_policy"] if not locals()[f]]
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            frappe.log_error(message=error_msg, title="Debug: Handle Override Validation Error")
            return {"success": False, "message": error_msg}

        try:
            from_date = frappe.utils.getdate(effective_from)
            to_date = frappe.utils.getdate(effective_to)
            if to_date < from_date:
                error_msg = "Effective To date cannot be before Effective From date"
                frappe.log_error(message=error_msg, title="Debug: Handle Override Date Error")
                return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Invalid date format: {str(e)}"
            frappe.log_error(message=error_msg, title="Debug: Handle Override Date Format Error")
            return {"success": False, "message": error_msg}

        for doctype in ["Leave Policy Assignment", "Leave Allocation", "Leave Ledger Entry"]:
            if not (frappe.has_permission(doctype, "write") and frappe.has_permission(doctype, "cancel")):
                error_msg = f"User {frappe.session.user} lacks permission to modify or cancel {doctype}"
                frappe.log_error(message=error_msg, title="Debug: Handle Override Permission Error")
                return {"success": False, "message": error_msg}

        filters = {
            "employee": employee,
            "docstatus": 1,
            "effective_from": ["<=", effective_to],
            "effective_to": [">=", effective_from],
        }
        if current_doc_name:
            filters["name"] = ["!=", current_doc_name]

        assignments = frappe.get_list(
            "Leave Policy Assignment",
            filters=filters,
            fields=["name", "effective_from", "effective_to", "leave_policy"]
        )

        frappe.log_error(
            message=f"Found {len(assignments)} overlapping assignments: {assignments}",
            title="Debug: Handle Override Assignments"
        )

        if not assignments:
            return {"success": True, "message": "No overlapping assignments to override"}

        for assignment in assignments:
            if assignment.leave_policy == leave_policy:
                error_msg = f"Cannot override with the same leave policy ({leave_policy}) in the same period."
                frappe.log_error(message=error_msg, title="Debug: Same Policy Error")
                return {"success": False, "message": error_msg}

        for assignment in assignments:
            leave_allocations = frappe.get_list(
                "Leave Allocation",
                filters={
                    "employee": employee,
                    "leave_policy_assignment": assignment.name,
                    "docstatus": 1
                },
                fields=["name", "from_date", "to_date", "leave_type", "expired"]
            )
            
            frappe.log_error(
                message=f"Found {len(leave_allocations)} leave allocations for assignment {assignment.name}: {leave_allocations}",
                title="Debug: Handle Override Leave Allocations"
            )

            for alloc in leave_allocations:
                try:
                    frappe.db.sql("""
                        UPDATE `tabLeave Ledger Entry` 
                        SET docstatus = 2 
                        WHERE transaction_name = %s 
                        AND transaction_type = 'Leave Allocation'
                        AND docstatus = 1
                    """, (alloc.name,))
                    
                    frappe.log_error(
                        message=f"Cancelled ledger entries for allocation {alloc.name} using direct SQL",
                        title="Debug: Direct SQL Ledger Cancel"
                    )
                except Exception as e:
                    frappe.log_error(
                        message=f"Failed to cancel ledger entries for allocation {alloc.name}: {str(e)}",
                        title="Debug: Ledger Cancel Error"
                    )
                    return {"success": False, "message": f"Failed to cancel ledger entries: {str(e)}"}

            for alloc in leave_allocations:
                try:
                    frappe.db.sql("""
                        UPDATE `tabLeave Allocation` 
                        SET docstatus = 2, expired = 0 
                        WHERE name = %s AND docstatus = 1
                    """, (alloc.name,))
                    
                    frappe.log_error(
                        message=f"Cancelled leave allocation {alloc.name} using direct SQL",
                        title="Debug: Direct SQL Allocation Cancel"
                    )
                except Exception as e:
                    frappe.log_error(
                        message=f"Failed to cancel leave allocation {alloc.name}: {str(e)}",
                        title="Debug: Allocation Cancel Error"
                    )
                    return {"success": False, "message": f"Failed to cancel leave allocation {alloc.name}: {str(e)}"}

        for assignment in assignments:
            try:
                frappe.db.sql("""
                    UPDATE `tabLeave Policy Assignment` 
                    SET docstatus = 2 
                    WHERE name = %s AND docstatus = 1
                """, (assignment.name,))
                
                frappe.log_error(
                    message=f"Cancelled assignment {assignment.name} using direct SQL",
                    title="Debug: Direct SQL Assignment Cancel"
                )
            except Exception as e:
                frappe.log_error(
                    message=f"Failed to cancel assignment {assignment.name}: {str(e)}",
                    title="Debug: Assignment Cancel Error"
                )
                return {"success": False, "message": f"Failed to cancel assignment {assignment.name}: {str(e)}"}

        frappe.db.commit()

        success_msg = f"Successfully cleared overlapping assignments, allocations, and ledger entries for employee {employee}. Leave applications and attendance remain intact."
        frappe.log_error(message=success_msg, title="Debug: Handle Override Success")
        return {"success": True, "message": success_msg}

    except Exception as e:
        frappe.log_error(
            message=f"Unexpected error in handle_leave_policy_override: {str(e)}",
            title="Debug: Handle Override Unexpected Error"
        )
        frappe.db.rollback()
        return {"success": False, "message": f"Server error: {str(e)}"}

class LeavePolicyAssignmentOverride(LeavePolicyAssignment):
    def validate(self):
        frappe.log_error(
            message=f"Validating LPA {self.name}, employee={self.employee}, from={self.effective_from}, to={self.effective_to}, policy={self.leave_policy}, override={self.custom_override_existing_assignment}, assignment_based_on={self.assignment_based_on}",
            title="Debug: LPA Validate"
        )
        if not frappe.session.user or frappe.session.user == "Guest":
            frappe.log_error(message="Invalid session during validation", title="Debug: LPA Validate Session Error")
            frappe.throw("Invalid session: Please log in again")

        if self.assignment_based_on == "Custom Range":
            if not self.effective_from or not self.effective_to:
                frappe.throw(_("Effective From and Effective To dates are mandatory for Custom Range."))
            if getdate(self.effective_to) < getdate(self.effective_from):
                frappe.throw(_("Effective To date cannot be before Effective From date."))
        elif self.assignment_based_on == "Leave Period":
            if not self.leave_period:
                frappe.throw(_("Leave Period is mandatory when Assignment Based On is Leave Period."))
        elif self.assignment_based_on == "Joining Date":
            if not self.effective_to:
                frappe.throw(_("Effective To date is mandatory for Joining Date."))
            date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
            if not date_of_joining:
                frappe.throw(_("No date of joining found for employee {0}. Please set it in the Employee record.").format(self.employee))
            self.effective_from = date_of_joining

        if self.assignment_based_on == "Leave Period" and self.leave_period:
            from_date, to_date = frappe.db.get_value("Leave Period", self.leave_period, ["from_date", "to_date"])
            self.effective_from = from_date
            self.effective_to = to_date
        elif self.assignment_based_on == "Joining Date":
            date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
            if not date_of_joining:
                frappe.throw(_("No date of joining found for employee {0}. Please set it in the Employee record.").format(self.employee))
            self.effective_from = date_of_joining

        if self.custom_override_existing_assignment:
            try:
                result = handle_leave_policy_override(
                    employee=self.employee,
                    effective_from=self.effective_from,
                    effective_to=self.effective_to,
                    current_doc_name=self.name,
                    leave_policy=self.leave_policy
                )
                if not result.get("success"):
                    frappe.log_error(f"Validation override failed: {result.get('message')}", title="Debug: Validation Override Error")
                    frappe.throw(result.get("message"))
                frappe.log_error(message=f"Validation override successful: {result.get('message')}", title="Debug: Validation Override Success")
            except Exception as e:
                frappe.log_error(f"Error in validation override: {str(e)}", title="Debug: Validation Override Error")
                frappe.throw(_("Failed to clear overlaps: {0}").format(str(e)))
        else:
            filters = {
                "employee": self.employee,
                "docstatus": 1,
                "effective_from": ["<=", self.effective_to],
                "effective_to": [">=", self.effective_from],
                "name": ["!=", self.name or ""]
            }
            overlaps = frappe.get_list(
                "Leave Policy Assignment",
                filters=filters,
                fields=["name", "effective_from", "effective_to", "leave_policy"]
            )
            if overlaps:
                for overlap in overlaps:
                    if overlap.leave_policy == self.leave_policy:
                        frappe.log_error(
                            message=f"Same policy overlap detected: {overlap}",
                            title="Debug: LPA Validate Same Policy"
                        )
                        frappe.throw(
                            _("Cannot assign the same leave policy ({0}) for Employee {1} in the same period {2} to {3}").format(
                                overlap.leave_policy, self.employee, overlap.effective_from, overlap.effective_to
                            )
                        )
                frappe.log_error(
                    message=f"Overlap detected: {overlaps}",
                    title="Debug: LPA Validate Overlap"
                )
                frappe.throw(
                    _("Leave Policy Assignment Overlap: Leave Policy: {0} already assigned for Employee {1} for period {2} to {3}").format(
                        overlaps[0].leave_policy, self.employee, overlaps[0].effective_from, overlaps[0].effective_to
                    )
                )
        super().validate()

class LeaveAllocationOverride(LeaveAllocation):
    def before_cancel(self):
        if not getattr(self, 'flags', {}).get('bypass_expiry_check', False):
            super().before_cancel()
        else:
            frappe.log_error(
                message=f"Bypassing all validations for Leave Allocation {self.name}",
                title="Debug: Leave Allocation Cancel"
            )

class LeaveLedgerEntryOverride(LeaveLedgerEntry):
    def before_cancel(self):
        if not getattr(self, 'flags', {}).get('bypass_expiry_check', False):
            super().before_cancel()
        else:
            frappe.log_error(
                message=f"Bypassing before_cancel validations for Leave Ledger Entry {self.name}",
                title="Debug: Leave Ledger Entry Before Cancel"
            )

    def on_cancel(self):
        if not getattr(self, 'flags', {}).get('bypass_expiry_check', False):
            super().on_cancel()
        else:
            frappe.log_error(
                message=f"Bypassing on_cancel validations for Leave Ledger Entry {self.name}",
                title="Debug: Leave Ledger Entry On Cancel"
            )
            if self.is_expired and self.transaction_name:
                frappe.db.set_value("Leave Allocation", self.transaction_name, "expired", 0)