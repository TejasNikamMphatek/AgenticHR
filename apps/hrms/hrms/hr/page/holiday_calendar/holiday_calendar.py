import frappe
import calendar
from datetime import datetime

@frappe.whitelist()
def getHolidayData():
    employee = get_employee()
    holiday_list = getHolidayList(employee[0]['holiday_list'])
    return [{'holiday_list' : holiday_list}]


def get_employee():
    user = frappe.session.user
    employee = frappe.get_all(
        "Employee",
        filters=[
            ["status", "=", "Active"],
            ["company_email", "=", user]
        ],
        fields=[
            "employee_name",
            "name as id",
            "holiday_list",
            "company"
        ],
        order_by="name"
    )
    
    if employee:
        return employee
    else:
        default_company = frappe.db.get_single_value("Global Defaults", "default_company")
        company_holiday_list = frappe.get_all("Company",filters={"name": default_company},fields=["default_holiday_list as holiday_list"])
        return company_holiday_list



def getHolidayList(holiday_list_name=None):
    # Fetch holidays from the database
    holiday_list = frappe.get_all(
        "Holiday",
        filters=[
            ["weekly_off", "=", "0"],
            ["parent", "=", holiday_list_name]
        ],
        fields=[
            "description",
            "holiday_date"
        ],
        order_by="holiday_date asc",
    )
    
    # Initialize a dictionary for all months in the year
    current_year = datetime.now().year
    grouped_holidays = {f"{calendar.month_abbr[month]} {current_year}": [] for month in range(1, 13)}
    
    # Group fetched holidays by month
    for holiday in holiday_list:
        # Parse the holiday date
        holiday_date = holiday["holiday_date"]
        month_name = holiday_date.strftime("%b %Y")  # Format as "Mar 2024"
        day_name = holiday_date.strftime("%a")  # Get day of the week, e.g., "Fri"
        
        # Format holiday details
        holiday_details = {
            "date": holiday_date.day,
            "day": day_name,
            "description": holiday["description"]
        }
        
        # Add holiday to the appropriate month
        if month_name in grouped_holidays:
            grouped_holidays[month_name].append(holiday_details)
    
    return grouped_holidays
