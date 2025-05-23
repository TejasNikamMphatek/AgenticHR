# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		filters = {}

	data = get_data(filters)
	columns = get_columns(filters) if len(data) else []

	return columns, data

def get_columns(filters):
	columns = [
				{
					"label": _("Employee"),
					"fieldname": "employee",
					"fieldtype": "Link",
					"options": "Employee",
					"width": 200,
				},
				{
					"label": _("Employee Name"),
					"fieldname": "employee_name",
					"width": 160,
				},
				{
					"label": _("Posting Date"),
                    "fieldname": "posting_date",
                    "fieldtype": "Date",
                    "width": 120,
				},
				{
					"label": _("Bank Name"),
					"fieldname": "bank_name",
					"width": 160,
				},
				{
					"label": _("Bank Account Number"),
					"fieldname": "bank_account_no",
					"width": 180,
				},
				{
					"label": _("Rounded Total"),
					"fieldname": "rounded_total",
					"fieldtype": "Currency",
					"width": 140,
				},
			]
	return columns


def get_data(filters):

	data = []
	conditions = get_conditions(filters)
	query = """
        SELECT 
            sal.employee, 
            sal.employee_name,
			sal.posting_date, 
            sal.bank_name, 
            sal.bank_account_no, 
            sal.rounded_total
        FROM 
            `tabSalary Slip` sal
        WHERE 
            sal.docstatus = 1 {conditions}
    """.format(conditions=conditions)
	
	entries = frappe.db.sql(query, as_dict=True)
	for entry in entries:
		data.append(entry)
	return data
	
def get_conditions(filters):
	conditions = ""
	if filters.get("employee"):
		conditions += " AND sal.employee = '{employee}'".format(
            employee=filters["employee"].replace("'", "\\'")
        )

	if filters.get("company"):
		conditions += " AND company = '%s'" % filters["company"].replace("'", "\\'")

	if filters.get("start_date"):
		conditions += " AND start_date >= '%s'" % filters["start_date"].replace("'","\\'")

	if filters.get("end_date"):
		conditions += " AND end_date <= '%s'" % filters["end_date"].replace("'","\\'")

	return conditions