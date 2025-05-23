# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


import frappe
from frappe import _

# from hrms.payroll.report.provident_fund_deductions.provident_fund_deductions import get_conditions


def execute(filters=None):
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
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 160,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 160,
		},

		{
			"label": _("Component"),
			"fieldname": "salary_component",
			"width": 160,
		},
		{
			"label": _("Amount"),
			 "fieldname": "amount", 
			 "fieldtype": "Currency", 
			 "width": 140
		},
	]

	return columns


def get_data(filters):

	data = []

	component_type_dict = frappe._dict(
		frappe.db.sql(
			"""
			SELECT 
				name, component_type 
			FROM 
				`tabSalary Component` 
			WHERE 
				name IN ('ESI', 'Employer ESI')
			"""
		)

	)

	if not len(component_type_dict):
		return []

	conditions = get_conditions(filters)

	entry = frappe.db.sql(
		""" select sal.employee, sal.employee_name, sal.start_date, sal.end_date, ded.salary_component, ded.amount
		from `tabSalary Slip` sal, `tabSalary Detail` ded
		where sal.name = ded.parent
		and ded.parentfield = 'deductions'
		and ded.parenttype = 'Salary Slip'
		and sal.docstatus = 1 %s
		and ded.salary_component in (%s)
	"""
		% (conditions, ", ".join(["%s"] * len(component_type_dict))),
		tuple(component_type_dict.keys()),
		as_dict=1,
	)

	for d in entry:
		employee = {"employee": d.employee, "start_date":d.start_date, "end_date": d.end_date ,"employee_name": d.employee_name,"salary_component":d.salary_component, "amount": d.amount}
		data.append(employee)
	return data

	
def get_conditions(filters):
    conditions = ""
	
    if filters.get("employee"):
        conditions += " AND employee = '%s'" % filters["employee"].replace("'", "\\'")
    return conditions
