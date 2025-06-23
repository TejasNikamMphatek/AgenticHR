import frappe
from frappe import _
import calendar
from datetime import datetime


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_holiday_data(filters)
	return columns, data


def get_columns():
	return [
		_("Holiday List") + ":Data:150",
		_("Holiday Date") + ":Date:120",
		_("Day") + ":Data:80",
		_("Description") + ":Data:250",
		_("Month Year") + ":Data:120",
		_("From Date") + ":Date:120",
		_("To Date") + ":Date:120",
	]


def get_holiday_data(filters):
	conditions, values = get_conditions(filters)
	
	query = """
		SELECT 
			h.parent as holiday_list,
			h.holiday_date,
			DAYNAME(h.holiday_date) as day_name,
			h.description,
			DATE_FORMAT(h.holiday_date, %s) as month_year,
			hl.from_date,
			hl.to_date
		FROM `tabHoliday` h
		LEFT JOIN `tabHoliday List` hl ON h.parent = hl.name
		WHERE h.weekly_off = 0 {conditions}
		ORDER BY h.parent, h.holiday_date ASC
	""".format(conditions=conditions)
	
	# Add the date format parameter
	query_values = ['%b %Y'] + values
	
	return frappe.db.sql(query, query_values, as_list=1)


def get_conditions(filters):
	conditions = ""
	values = []
	
	if filters.get("holiday_list"):
		conditions += " AND h.parent = %s"
		values.append(filters["holiday_list"])
	else:
		default_data = get_default_data()
		if default_data and default_data.get("holiday_list"):
			conditions += " AND h.parent = %s"
			values.append(default_data["holiday_list"])
		else:
			# If no default holiday list found, return condition that matches nothing
			conditions += " AND 1=0"
	
	# Add date range filters if provided
	if filters.get("from_date"):
		conditions += " AND h.holiday_date >= %s"
		values.append(filters["from_date"])
		
	if filters.get("to_date"):
		conditions += " AND h.holiday_date <= %s"
		values.append(filters["to_date"])
	
	# Add year filter if provided
	if filters.get("year"):
		conditions += " AND YEAR(h.holiday_date) = %s"
		values.append(filters["year"])
	
	return conditions, values


def get_default_data():
	try:
		default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not default_company:
			return {}

		company_doc = frappe.get_all(
			"Company",
			filters={"name": default_company},
			fields=["default_holiday_list as holiday_list", "name as default_company"],
			limit=1
		)

		return company_doc[0] if company_doc else {}

	except Exception as e:
		frappe.log_error(f"Error in get_default_data: {str(e)}")
		return {}