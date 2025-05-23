# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _

def execute(filters=None):
    data = get_data(filters)
    columns = get_columns(filters) if data else []
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
            "label": _("Payroll Period"),
            "fieldname": "payroll_period",
            "fieldtype": "Link",
            "options": "Employee Tax Exemption Declaration",
            "width": 140,
        },
		{
            "label": _("Total Actual Amount"),
            "fieldname": "total_actual_amount",
            "fieldtype": "Currency",
            "width": 180,
        },
		{
            "label": _("Total Exemption Amount"),
            "fieldname": "exemption_amount",
            "fieldtype": "Currency",
            "width": 180,
        },
    ]

    return columns

def get_data(filters):
    data = []
    conditions = get_conditions(filters)

    query = """
        SELECT 
            name,
            employee, 
            employee_name, 
            payroll_period,
            total_actual_amount,
            exemption_amount
        FROM 
            `tabEmployee Tax Exemption Proof Submission` 
        WHERE 
            docstatus = 1 {conditions}
    """.format(conditions=conditions)

    entries = frappe.db.sql(query, as_dict=1)

    for d in entries:
        # declarations = get_declaration_category(d.name)
        # if not declarations:
        #     continue  
          
        employee = {
            "employee": d.employee,
            "employee_name": d.employee_name,
            "payroll_period": d.payroll_period,
            "total_actual_amount": d.total_actual_amount,
            "exemption_amount": d.exemption_amount,
        }
        # employee = {**employee, **declarations}
        data.append(employee)
    return data

def get_conditions(filters):
    conditions = ""
    if filters.get("employee"):
        conditions += " AND employee = '{0}'".format(filters["employee"].replace("'", "\\'"))
    if filters.get("company"):
        conditions += " AND company = '{0}'".format(filters["company"].replace("'", "\\'"))
    if filters.get("payroll_period"):
        conditions += " AND payroll_period = '{0}'".format(filters["payroll_period"].replace("'", "\\'"))
    return conditions

# def get_declaration_category(name):
#     declarations = frappe.db.get_all(
#         "Employee Tax Exemption Declaration Category",
#         filters={"parent": name},
#         fields=["exemption_category", "exemption_sub_category", "max_amount", "amount"],
#         ignore_ifnull=False
#     )

#     declaration_obj = {}
#     for d_val in declarations:
#         sub_decla = {
#             "exemption_category": d_val['exemption_category'],
#             "exemption_sub_category": d_val['exemption_sub_category'],
#             "max_amount": d_val['max_amount'],
#             "amount": d_val['amount'],
#         }
        
#         declaration_obj[d_val['exemption_category']] = sub_decla
        
#     return declaration_obj
