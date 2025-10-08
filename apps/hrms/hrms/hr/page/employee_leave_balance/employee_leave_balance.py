import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, formatdate, nowdate, add_years
from frappe.desk.query_report import get_columns_dict
import json
from datetime import datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_details

from frappe.utils import getdate, add_days, flt

@frappe.whitelist()
def get_employee_leave_balance(employee=None, leave_type=None, year=None):
    
    if not employee:
        emp = get_employee_details(frappe.session.user)
        if emp:
            employee = emp.get("name")
            employee_name = emp.get("employee_name")
            company_email = emp.get("company_email")
        else:
            employee = None
        
        
    try:
        # Validate permissions first
        validate_permissions()
        
        filters = build_filters(employee, leave_type, year)
        data = get_leave_balance_data(filters)
        return data
        
    except frappe.ValidationError:
       
        raise
    except Exception as e:
        frappe.log_error(f"Error in get_employee_leave_balance: {str(e)}")
        frappe.logger().error(f"Detailed error: {str(e)}")
        frappe.throw(_("Error fetching leave balance data: {0}").format(str(e)))


def get_employee_details(user):
    employee = frappe.get_all(
        "Employee",
        filters=[
            ["status", "=", "Active"],
            ["company_email", "=", user]
        ],
        fields=["name", "employee_name", "company_email"],
        limit_page_length=1
    )
    return employee[0] if employee else None


def build_filters(employee, leave_type, year):
    filters = {}
    
    if employee:
        filters['employee'] = employee
    
    if leave_type:
        filters['leave_type'] = leave_type
    
   
    current_year = datetime.now().year
    filters['year'] = int(year) if year else current_year
    
    filters['from_date'] = f"{filters['year']}-01-01"
    filters['to_date'] = f"{filters['year']}-12-31"
    
    return filters

def format_leave_value(value):
    """Format leave value to show as integer or 1 decimal place."""
    value = flt(value)
    # If it's effectively an integer (like 4.0), show as 4
    if value.is_integer():
        return int(value)
    # Else show one decimal (like 4.5)
    return round(value, 1)

def get_leave_balance_data(filters):
    try:
        from_date = getdate(filters["from_date"])
        to_date = getdate(filters["to_date"])

        # Calculate the reference date for leave details (as of end of year if past, else today)
        current_year = datetime.now().year
        if filters['year'] < current_year:
            calc_date = getdate(f"{filters['year']}-12-31")
        else:
            calc_date = getdate(nowdate())

        # Get unique employees with allocations in the period
        if filters.get("employee"):
            employees = [filters["employee"]]
        else:
            employees_query = """
                SELECT DISTINCT employee 
                FROM `tabLeave Allocation` la
                WHERE la.docstatus = 1 
                AND la.from_date <= %(to_date)s 
                AND la.to_date >= %(from_date)s
            """
            emp_list = frappe.db.sql(employees_query, filters, as_list=True)
            employees = [e[0] for e in emp_list]

        final_data = []

        for emp in employees:
            try:
                # Use the same method as Leave Application dashboard, with calculated date
                leave_details_resp = get_leave_details(emp, calc_date)
                allocation = leave_details_resp.get("leave_allocation", {})

                emp_info = frappe.db.get_value(
                    "Employee", 
                    emp, 
                    ["employee_name", "designation", "department", "company"], 
                    as_dict=1
                )

                for lt, details in allocation.items():
                    if filters.get("leave_type") and lt != filters["leave_type"]:
                        continue

                    leave_type_name = frappe.db.get_value("Leave Type", lt, "leave_type_name") or lt

                    # Get leave applications for details
                    leave_applications = get_leave_application_details(emp, lt, filters)

                    row = {
                        "employee": emp,
                        "employee_name": emp_info.get("employee_name"),
                        "designation": emp_info.get("designation"),
                        "department": emp_info.get("department"),
                        "company": emp_info.get("company"),
                        "leave_type": lt,
                        "leave_type_name": leave_type_name,
                        "total_leaves": format_leave_value(details["total_leaves"]),
                        "expired_leaves": format_leave_value(details["expired_leaves"]),
                        "leaves_taken": format_leave_value(details["leaves_taken"]),
                        "leaves_pending_approval": format_leave_value(details["leaves_pending_approval"]),
                        "remaining_leaves": format_leave_value(details["remaining_leaves"]),
                        "total_applications": len(leave_applications),
                        "leave_applications": leave_applications,
                    }

                    final_data.append(row)

            except Exception as e:
                frappe.logger().error(f"[get_leave_balance_data] Error processing {emp}: {str(e)}")

        return final_data

    except Exception as e:
        frappe.logger().error(f"Error in get_leave_balance_data(): {str(e)}")
        raise

def get_leave_application_details(employee, leave_type, filters):
    """
    Get detailed leave application data for specific employee and leave type
    
    Args:
        employee (str): Employee ID
        leave_type (str): Leave Type
        filters (dict): Additional filters
    
    Returns:
        list: Leave application details
    """
    try:
        conditions = [
            "la.docstatus = 1", 
            "la.employee = %(employee)s", 
            "la.leave_type = %(leave_type)s",
            "la.status = 'Approved'"
        ]
        values = {'employee': employee, 'leave_type': leave_type}
        
        # Add date range filter
        if filters.get('from_date') and filters.get('to_date'):
            conditions.append("la.from_date >= %(from_date)s")
            conditions.append("la.to_date <= %(to_date)s")
            values['from_date'] = filters['from_date']
            values['to_date'] = filters['to_date']
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT 
                la.name,
                la.posting_date,
                la.from_date,
                la.to_date,
                la.total_leave_days,
                la.status,
                la.leave_type,
                la.description,
                la.leave_approver,
                la.follow_via_email
            FROM 
                `tabLeave Application` la
            WHERE 
                {where_clause}
            ORDER BY 
                la.from_date DESC
            
        """
        
        return frappe.db.sql(query, values, as_dict=True)
        
    except Exception as e:
        frappe.logger().error(f"Error in get_leave_application_details: {str(e)}")
        return []

def validate_permissions():
    if not frappe.has_permission('Employee', 'read'):
        frappe.throw(_("You don't have permission to access employee data"))
    
    if not frappe.has_permission('Leave Application', 'read'):
        frappe.throw(_("You don't have permission to access leave application data"))

@frappe.whitelist()
def export_leave_balance(employee=None, leave_type=None, year=None):
   
    try:
        validate_permissions()
        
        from frappe.utils.xlsxutils import make_xlsx
        
        filters = build_filters(employee, leave_type, year)
        data = get_leave_balance_data(filters)
        
        if not data:
            frappe.throw(_("No data found to export"))
        
        # Prepare data for Excel - matching Allocated Leaves
        columns = [
            _("Employee ID"),
            _("Employee Name"),
            _("Department"),
            _("Designation"),
            _("Leave Type"),
            _("Total Allocated Leaves"),
            _("Expired Leaves"),
            _("Used Leaves"),
            _("Leaves Pending Approval"),
            _("Available Leaves"),
            _("Total Applications")
        ]
        
        rows = []
        for row in data:
            rows.append([
                row.get('employee'),
                row.get('employee_name'),
                row.get('department'),
                row.get('designation'),
                row.get('leave_type_name'),
                row.get('total_leaves', 0),
                row.get('expired_leaves', 0),
                row.get('leaves_taken', 0),
                row.get('leaves_pending_approval', 0),
                row.get('remaining_leaves', 0),
                row.get('total_applications', 0)
            ])
        
        # Create Excel file
        xlsx_data = make_xlsx([columns] + rows, "Employee Leave Balance")
        
        # Save file
        filename = f"employee_leave_balance_{filters['year']}_{frappe.utils.nowdate()}.xlsx"
        
        # Create file record
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "content": xlsx_data.getvalue(),
            "is_private": 1
        })
        file_doc.insert()
        
        return {
            'file_url': file_doc.file_url,
            'filename': filename
        }
        
    except Exception as e:
        frappe.log_error(f"Error in export_leave_balance: {str(e)}")
        frappe.throw(_("Error exporting data: {0}").format(str(e)))

@frappe.whitelist()
def get_dashboard_data():
   
    try:
        validate_permissions()
        
        current_date = nowdate()
        current_year = datetime.now().year
        
        # Get total active employees
        total_employees = frappe.db.count('Employee', {'status': 'Active'})
        
        # Get employees on leave today
        employees_on_leave = frappe.db.sql("""
            SELECT COUNT(DISTINCT employee) as count
            FROM `tabLeave Application`
            WHERE status = 'Approved'
            AND docstatus = 1
            AND %s BETWEEN from_date AND to_date
        """, (current_date,), as_dict=True)[0].get('count', 0)
        
        # Get pending leave applications
        pending_applications = frappe.db.count('Leave Application', {
            'status': 'Open',
            'docstatus': 0
        })
        
        # Get employees with low leave balance (less than 5 days)
        low_balance_query = """
            SELECT COUNT(*) as count
            FROM (
                SELECT 
                    emp.name as employee,
                    lt.name as leave_type,
                    COALESCE(
                        (SELECT SUM(total_leaves_allocated) 
                         FROM `tabLeave Allocation` 
                         WHERE employee = emp.name 
                         AND leave_type = lt.name 
                         AND docstatus = 1
                         AND YEAR(from_date) = %s), 0
                    ) - COALESCE(
                        (SELECT SUM(total_leave_days)
                         FROM `tabLeave Application` 
                         WHERE employee = emp.name 
                         AND leave_type = lt.name 
                         AND docstatus = 1 
                         AND status = 'Approved'
                         AND YEAR(from_date) = %s), 0
                    ) as balance
                FROM `tabEmployee` emp
                CROSS JOIN `tabLeave Type` lt
                WHERE emp.status = 'Active'
                HAVING balance > 0 AND balance < 5
            ) as low_balance_data
        """
        
        low_balance_result = frappe.db.sql(low_balance_query, (current_year, current_year), as_dict=True)
        low_balance_employees = low_balance_result[0].get('count', 0) if low_balance_result else 0
        
        # Get leave applications this month
        monthly_applications = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabLeave Application`
            WHERE MONTH(creation) = MONTH(%s)
            AND YEAR(creation) = YEAR(%s)
            AND docstatus = 1
        """, (current_date, current_date), as_dict=True)[0].get('count', 0)
        
        return {
            'total_employees': total_employees,
            'employees_on_leave': employees_on_leave,
            'pending_applications': pending_applications,
            'low_balance_employees': low_balance_employees,
            'monthly_applications': monthly_applications,
            'current_date': current_date,
            'current_year': current_year
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_dashboard_data: {str(e)}")
        return {}

@frappe.whitelist()
def get_employee_suggestions(txt):
    """
    Get employee suggestions for autocomplete
    
    Args:
        txt (str): Search text
    
    Returns:
        list: Employee suggestions
    """
    try:
        return frappe.db.sql("""
            SELECT name, employee_name
            FROM `tabEmployee`
            WHERE status = 'Active'
            AND (name LIKE %(txt)s OR employee_name LIKE %(txt)s)
            ORDER BY employee_name
            LIMIT 20
        """, {'txt': f'%{txt}%'}, as_dict=True)
        
    except Exception as e:
        frappe.logger().error(f"Error in get_employee_suggestions: {str(e)}")
        return []

@frappe.whitelist()
def get_leave_type_suggestions(txt):
    """
    Get leave type suggestions for autocomplete
    
    Args:
        txt (str): Search text
    
    Returns:
        list: Leave type suggestions
    """
    try:
        return frappe.db.sql("""
            SELECT name, leave_type_name
            FROM `tabLeave Type`
            WHERE (name LIKE %(txt)s OR leave_type_name LIKE %(txt)s)
            ORDER BY leave_type_name
            LIMIT 20
        """, {'txt': f'%{txt}%'}, as_dict=True)
        
    except Exception as e:
        frappe.logger().error(f"Error in get_leave_type_suggestions: {str(e)}")
        return []