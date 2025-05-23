# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_employees(filters)
	return columns, data


def get_columns():
	return [
		_("Employee") + ":Link/Employee:100",
		_("Name") + ":Data:200",
		_("Currency") + ":Link/Currency:80",
		_("Company") + ":Link/Company:180",
		_("Promotion Date") + ":Date/Promotion Date:120",
		_("Current CTC") + ":Currency/Current CTC:120",
		_("Revised CTC") + ":Currency/Revised CTC:120",
	]


def get_employees(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql(
		"""select employee, employee_name, salary_currency, company,
	promotion_date, current_ctc, revised_ctc from `tabEmployee Promotion` where docstatus = '1' %s"""
		% conditions,
		as_list=1,
	)

def get_conditions(filters):
    conditions = ""
	
    if filters.get("employee"):
        conditions += " AND employee = '%s'" % filters["employee"].replace("'", "\\'")

    if filters.get("company"):
        conditions += " AND company = '%s'" % filters["company"].replace("'", "\\'")

    return conditions
