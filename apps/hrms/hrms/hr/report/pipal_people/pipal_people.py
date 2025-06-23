import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_employees(filters)
	return columns, data

def get_columns():
	return [
		_("Employee Number") + "::Data:100",
		_("Employee Name") + "::Data:200",
		_("Date of Birth") + ":Data:120",
		_("Company") + ":Data:120",
		_("Reports To Name") + ":Data:100",
		_("Date of Joining") + ":Date:100",
	]

def get_employees(filters):
	conditions, values = get_conditions(filters)

	query = f"""
		SELECT 
			employee,
			employee_name,
			date_of_birth, 
			company, 
			report_to_name, 
			date_of_joining
		FROM `tabEmployee`
		WHERE status = 'Active' {conditions}
		ORDER BY employee_number ASC limit 10
	"""
	
	raw_data = frappe.db.sql(query, values, as_dict=True)
	data = []

	for row in raw_data:
		# Format date_of_birth as "01 Jan"
		dob = row.date_of_birth.strftime("%d %b") if row.date_of_birth else ""
		data.append([
			row.employee,
			row.employee_name,
			dob,
			row.company,
			row.report_to_name,
			row.date_of_joining
		])

	return data

def get_conditions(filters):
	conditions = ""
	values = []

	if filters.get("employee"):
		conditions += " AND employee = %s"
		values.append(filters["employee"])

	return conditions, values
