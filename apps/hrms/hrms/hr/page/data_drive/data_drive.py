import frappe
from frappe.query_builder.functions import Count

@frappe.whitelist()
def getDataDrive(company=None, employee=None, aadhar_verified=None):
    company = frappe.form_dict.get("company", company)
    employee = frappe.form_dict.get("employee", employee)
    aadhar_verified = frappe.form_dict.get("aadhar_verified", aadhar_verified)
    drive_data = getEmployeeDataDrive(company,employee,aadhar_verified)
    # first_page_data = get_paginated_employee_data(page=1, page_size=20)

    return [
        {
            "drive_data" : drive_data,
        }
    ]


def getEmployeeDataDrive(company=None, employee=None, aadhar_verified=None):
    filters = [["status", "=", "Active"], ["user_id", "!=", ""]]

    if company:
        filters.append(["company", "=", company])
    if employee:
        filters.append(["employee", "=", employee])
    if aadhar_verified:
        filters.append(["aadhar_verified", "=", aadhar_verified])

    drive_data =frappe.get_all(
		"Employee",
		filters = filters,
		fields=[
			"employee_name",
			"name as id",
			"designation",
            "aadhar_number",
            "name_on_aadhar",
            "attach_aadhar",
            "aadhar_verified"
		],
		order_by="name desc",
        limit=100,
	)
    return drive_data

def get_paginated_employee_data(page=1, page_size=20):
    limit_start = (page - 1) * page_size  # Calculate the offset
    drive_data = frappe.get_all(
        "Employee",
        filters=[
            ["status", "=", "Active"],
        ],
        fields=[
            "employee_name",
            "name as id",
            "designation",
            "aadhar_number",
            "name_on_aadhar",
            "attach_aadhar",
            "aadhar_verified"
        ],
        order_by="aadhar_number desc",  # Order by aadhar_number in descending order
        limit_start=limit_start,        # Offset for pagination
        limit_page_length=page_size     # Number of records per page
    )
    return drive_data
