import frappe
import calendar
from datetime import datetime

@frappe.whitelist()
def getHolidayData(start=None, hlist=None):
    if not hlist:
        hlist = frappe.form_dict.get("hlist")

    employee = get_employee()
    holiday_list_name = hlist or (employee[0]['holiday_list'] if employee else None)
    
    holiday_list = getHolidayList(holiday_list_name)
    holiday_list_names = getHolidayListNames()
    
    return [{'holiday_list': holiday_list, "holiday_list_names": holiday_list_names}]


def get_employee():
    user = frappe.session.user
    
    try:
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
            # Fallback to default company holiday list
            default_company = frappe.db.get_single_value("Global Defaults", "default_company")
            if default_company:
                company_holiday_list = frappe.get_all(
                    "Company",
                    filters={"name": default_company},
                    fields=["default_holiday_list as holiday_list"]
                )
                return company_holiday_list
            else:
                return []
                
    except Exception as e:
        frappe.log_error(f"Error getting employee data: {str(e)}")
        return []


def getHolidayList(holiday_list_name=None):
    if not holiday_list_name:
        return {}
    try:
        # Fetch holidays from the database
        holiday_list = frappe.get_all(
            "Holiday",
            filters=[
                ["weekly_off", "=", "0"],
                ["parent", "=", holiday_list_name],
            ],
            fields=[
                "description",
                "holiday_date"
            ],
            order_by="holiday_date asc",
        )

        # Step 1: Identify all years in the holiday list
        years = set()
        for holiday in holiday_list:
            years.add(holiday["holiday_date"].year)

        # Step 2: Initialize all month-year combinations for each year
        grouped_holidays = {}
        for year in years:
            for month in range(1, 13):
                month_year = f"{calendar.month_abbr[month]} {year}"
                grouped_holidays[month_year] = []

        # Step 3: Populate the holidays into the correct group
        for holiday in holiday_list:
            holiday_date = holiday["holiday_date"]
            month_year = holiday_date.strftime("%b %Y")
            day_name = holiday_date.strftime("%a")

            holiday_details = {
                "date": holiday_date.day,
                "day": day_name,
                "description": holiday["description"]
            }

            grouped_holidays[month_year].append(holiday_details)

        # Optional: Sort the grouped keys (month-year) if needed
        grouped_holidays = dict(sorted(
            grouped_holidays.items(),
            key=lambda x: datetime.strptime(x[0], "%b %Y")
        ))

        return grouped_holidays

    except Exception as e:
        frappe.log_error(f"Error getting holiday list: {str(e)}")
        return {}


def getHolidayListNames():
    try:
        holiday_list = frappe.get_all(
            "Holiday List",
            fields=[
                "holiday_list_name",
            ],
            order_by="from_date asc",
        )
        return holiday_list
        
    except Exception as e:
        frappe.log_error(f"Error getting holiday list names: {str(e)}")
        return []
    