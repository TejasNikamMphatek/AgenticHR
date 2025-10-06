import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, formatdate, nowdate, add_years
from frappe.desk.query_report import get_columns_dict
import json
from datetime import datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_details
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on, get_leaves_for_period
from hrms.hr.doctype.leave_application.leave_application import (
	get_leave_balance_on,
	get_leaves_for_period
)

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
		values = {"from_date": filters["from_date"], "to_date": filters["to_date"]}

		if filters.get("employee"):
			values["employee"] = filters["employee"]
		if filters.get("leave_type"):
			values["leave_type"] = filters["leave_type"]

		allocations = get_employees_with_allocated_leave_types(filters)
		final_data = []

		for row in allocations:
			try:
				employee = row["employee"]
				leave_type = row["leave_type"]

				# Opening as of 1 day before period
				opening = get_leave_balance_on(employee, leave_type, add_days(from_date, -1))

				# Fetch allocation range for this employee & leave type
				allocation_data = get_leave_allocation_data(employee, leave_type, filters["year"])
				allocation_to_date = allocation_data.get("allocation_to_date")
				allocation_from_date = allocation_data.get("allocation_from_date")

				# Adjust effective end date to avoid false expiry
				effective_to_date = to_date
				if allocation_to_date:
					alloc_to = getdate(allocation_to_date)
					if alloc_to < to_date:
						effective_to_date = alloc_to

				# Calculate final balance
				final_balance = get_leave_balance_on(employee, leave_type, effective_to_date)

				# Leaves taken during the period
				taken = get_leaves_for_period(employee, leave_type, from_date, effective_to_date) * -1

				# Total allocated
				total_allocated = allocation_data.get("total_allocated", 0)
				new_allocated = allocation_data.get("new_allocated", total_allocated)

				# Expired leaves
				expired_leaves = 0
				if allocation_to_date and getdate(allocation_to_date) < to_date:
					expired_leaves = max(total_allocated - taken, 0)

				# Leave Applications
				leave_applications = get_leave_application_details(employee, leave_type, filters)

				row.update({
					"opening_balance": format_leave_value(opening),
					"total_leaves_taken": format_leave_value(taken),
					"balance": format_leave_value(final_balance),
					"total_allocated": format_leave_value(total_allocated),
					"new_allocated": format_leave_value(new_allocated),
					"total_applications": len(leave_applications),
					"utilization_percentage": calculate_utilization_percentage(taken, opening + new_allocated),
					"status": get_balance_status(final_balance),
					"leave_applications": leave_applications,
					"total_leaves_expired": format_leave_value(expired_leaves)
				})

				final_data.append(row)

			except Exception as e:
				frappe.logger().error(f"[get_leave_balance_data] Error processing {row['employee']}, {row['leave_type']}: {str(e)}")

		return final_data

	except Exception as e:
		frappe.logger().error(f"Error in get_leave_balance_data(): {str(e)}")
		raise

def get_leave_application_count(employee, leave_type, filters):
    try:
        return frappe.db.count("Leave Application", {
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "status": "Approved",
            "from_date": (">=", filters["from_date"]),
            "to_date": ("<=", filters["to_date"])
        })
    except:
        return 0

def get_employees_with_allocated_leave_types(filters):
    query = """
        SELECT 
            la.employee,
            emp.employee_name,
            emp.designation,
            emp.department,
            emp.company,
            la.leave_type,
            lt.leave_type_name
        FROM `tabLeave Allocation` la
        INNER JOIN `tabEmployee` emp ON la.employee = emp.name
        INNER JOIN `tabLeave Type` lt ON la.leave_type = lt.name
        WHERE la.docstatus = 1
        AND la.from_date <= %(to_date)s
        AND la.to_date >= %(from_date)s
    """

    if filters.get("employee"):
        query += " AND la.employee = %(employee)s"

    if filters.get("leave_type"):
        query += " AND la.leave_type = %(leave_type)s"

    return frappe.db.sql(query, filters, as_dict=True)

def get_employees_with_allocations_only(filters):
    
    try:
        conditions = ["lalloc.docstatus = 1"]
        values = {}
        
        # Add year filter for allocations
        conditions.append("YEAR(lalloc.from_date) = %(year)s")
        values['year'] = filters['year']
        
        # Add employee filter
        if filters.get('employee'):
            conditions.append("lalloc.employee = %(employee)s")
            values['employee'] = filters['employee']
        
        # Add leave type filter
        if filters.get('leave_type'):
            conditions.append("lalloc.leave_type = %(leave_type)s")
            values['leave_type'] = filters['leave_type']
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT DISTINCT
                lalloc.employee,
                emp.employee_name,
                emp.designation,
                emp.department,
                emp.company,
                lalloc.leave_type,
                lt.leave_type_name,
                0 as total_leaves_taken,
                0 as total_applications,
                NULL as earliest_leave_date,
                NULL as latest_leave_date
            FROM 
                `tabLeave Allocation` lalloc
            INNER JOIN 
                `tabEmployee` emp ON lalloc.employee = emp.name
            INNER JOIN 
                `tabLeave Type` lt ON lalloc.leave_type = lt.name
            WHERE 
                {where_clause}
            ORDER BY 
                emp.employee_name, lalloc.leave_type
        """
    
        data = frappe.db.sql(query, values, as_dict=True)
        
        # Process each row
        for row in data:
            allocation_data = get_leave_allocation_data(row.employee, row.leave_type, filters['year'])
            row.update(allocation_data)
            
            row['balance'] = flt(row.get('total_allocated', 0))
            row['leave_applications'] = []
            row['utilization_percentage'] = 0
            row['status'] = get_balance_status(row['balance'])
        
        return data
        
    except Exception as e:
        frappe.logger().error(f"Error in get_employees_with_allocations_only: {str(e)}")
        return []

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
            "la.leave_type = %(leave_type)s"
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

def get_leave_allocation_data(employee, leave_type, year):
    """
    Get leave allocation data for specific employee and leave type for a given year
    
    Args:
        employee (str): Employee ID
        leave_type (str): Leave Type
        year (int): Year
    
    Returns:
        dict: Allocation data
    """
    try:
        allocation_data = frappe.db.sql("""
            SELECT 
                SUM(total_leaves_allocated) as total_allocated,
                SUM(carry_forward) as carry_forward,
                SUM(new_leaves_allocated) as new_allocated,
                MAX(from_date) as allocation_from_date,
                MAX(to_date) as allocation_to_date
            FROM 
                `tabLeave Allocation`
            WHERE 
                employee = %s 
                AND leave_type = %s 
                AND docstatus = 1
                AND YEAR(from_date) = %s
        """, (employee, leave_type, year), as_dict=True)
        
        if allocation_data and allocation_data[0] and allocation_data[0].get('total_allocated'):
            return {
                'total_allocated': flt(allocation_data[0].get('total_allocated', 0)),
                'carry_forward': flt(allocation_data[0].get('carry_forward', 0)),
                'new_allocated': flt(allocation_data[0].get('new_allocated', 0)),
                'allocation_from_date': allocation_data[0].get('allocation_from_date'),
                'allocation_to_date': allocation_data[0].get('allocation_to_date')
            }
        
        return {
            'total_allocated': 0,
            'carry_forward': 0,
            'new_allocated': 0,
            'allocation_from_date': None,
            'allocation_to_date': None
        }
        
    except Exception as e:
        frappe.logger().error(f"Error in get_leave_allocation_data: {str(e)}")
        return {
            'total_allocated': 0,
            'carry_forward': 0,
            'new_allocated': 0,
            'allocation_from_date': None,
            'allocation_to_date': None
        }

def calculate_utilization_percentage(leaves_taken, total_allocated):
    """
    Calculate leave utilization percentage
    
    Args:
        leaves_taken (float): Number of leaves taken
        total_allocated (float): Total leaves allocated
    
    Returns:
        float: Utilization percentage
    """
    if not total_allocated or total_allocated == 0:
        return 0
    
    return round((flt(leaves_taken) / flt(total_allocated)) * 100, 2)

def get_balance_status(balance):
    """
    Get status based on leave balance
    
    Args:
        balance (float): Leave balance
    
    Returns:
        str: Status (Good/Medium/Low/Critical)
    """
    balance = flt(balance)
    
    if balance <= 0:
        return "Critical"
    elif balance <= 2:
        return "Low"
    elif balance <= 5:
        return "Medium"
    else:
        return "Good"

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
        
        # Prepare data for Excel
        columns = [
            _("Employee ID"),
            _("Employee Name"),
            _("Department"),
            _("Designation"),
            _("Leave Type"),
            _("Total Allocated"),
            _("Leaves Taken"),
            _("Balance"),
            _("Utilization %"),
            _("Status"),
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
                row.get('total_allocated', 0),
                row.get('total_leaves_taken', 0),
                row.get('balance', 0),
                row.get('utilization_percentage', 0),
                row.get('status'),
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