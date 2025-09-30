# Copyright (c) 2013, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    if not filters.get("company"):
        frappe.throw(_("{0} is mandatory").format(_("Company")))

    columns = get_columns()
    employees = get_employees(filters)
    parameters_result = get_parameters(filters)
    parameters = [p for p in parameters_result if p]

    chart = get_chart_data(parameters, employees, filters)
    return columns, employees, None, chart


def get_columns():
    return [
        _("Employee") + ":Data/Employee:120",
        _("Name") + ":Data:200",
        _("Date of Birth") + ":Date:100",
        _("Branch") + ":Data/Branch:120",
        _("Department") + ":Data/Department:120",
        _("Designation") + ":Data/Designation:120",
        _("Gender") + "::100",
        _("Company") + ":Data/Company:120",
    ]


def get_conditions(filters):
    param_field = filters.get("parameter").lower().replace(" ", "_")
    conditions = f" AND {param_field} IS NOT NULL"

    if filters.get("company"):
        conditions += " AND company = '%s'" % filters["company"].replace("'", "\\'")
    return conditions


def get_employees(filters):
    conditions = get_conditions(filters)
    return frappe.db.sql(
        f"""SELECT name, employee_name, date_of_birth,
            branch, department, designation,
            gender, company 
            FROM `tabEmployee` 
            WHERE status='Active' {conditions}""",
        as_list=1,
    )


def get_parameters(filters):
    parameter = "Employee Grade" if filters.get("parameter") == "Grade" else filters.get("parameter")
    return frappe.db.sql(f"SELECT name FROM `tab{parameter}`", as_list=1)


def get_chart_data(parameters, employees, filters):
    if not parameters:
        parameters = []

    labels = []
    values = []
    param_field = filters.get("parameter").lower().replace(" ", "_")

    for param in parameters:
        if param:
            total = frappe.db.sql(
                f"""SELECT COUNT(*) FROM `tabEmployee` 
                    WHERE {param_field} = %s AND company = %s""",
                (param[0], filters.get("company")),
                as_list=1,
            )
            count = total[0][0] if total else 0
            if count:
                labels.append(param[0])
                values.append(count)

    total_employee = frappe.db.count("Employee", {"status": "Active"})
    others = total_employee - sum(values)
    labels.append("Not Set")
    values.append(others)

    chart = {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Employees", "values": values}],
        },
        "type": "bar",
        "barOptions": {"spaceRatio": 0.5},
        "height": 400,
    }
    return chart
