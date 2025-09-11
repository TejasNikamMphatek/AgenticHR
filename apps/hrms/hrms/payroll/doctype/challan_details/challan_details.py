# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta
from datetime import datetime
from frappe.utils import (getdate)

class ChallanDetails(Document):

    QUARTER_MAPPING = {
        frozenset({"Apr", "May", "Jun"}): "1st_quarter_april_june",
        frozenset({"Jul", "Aug", "Sep"}): "2nd_quarter_july_sep",
        frozenset({"Oct", "Nov", "Dec"}): "3rd_quarter_oct_dec",
        frozenset({"Jan", "Feb", "Mar"}): "4th_quarter_jan_mar",
    }

    def before_insert(self):
        self.validate_year_month()

    def validate_year_month(self):
        if not self.payroll_period:
            return 

        if not self.payroll_month or not self.payroll_year:
            frappe.throw("Payroll Month and Payroll Year must be provided for validation.")

        payroll_info = frappe.get_all(
            "Payroll Period",
            filters={"name": self.payroll_period},
            fields=["start_date", "end_date"],
            limit=1,
        )

        if not payroll_info:
            frappe.throw(f"Payroll Period {self.payroll_period} not found.")

        start_date_str = payroll_info[0].start_date
        end_date_str = payroll_info[0].end_date

      
        if not start_date_str or not end_date_str:
            frappe.throw("Payroll Period does not have valid start or end dates.")

        try:
            start_date = getdate(start_date_str)
            end_date = getdate(end_date_str)
        except ValueError as ve:
            frappe.throw(f"Invalid date format in Payroll Period")

        month_number = datetime.strptime(self.payroll_month, "%b").month
        check_date = getdate(datetime(self.payroll_year, month_number, 1))

        if not (start_date <= check_date <= end_date):
            frappe.throw(
                f"<b>Payroll Month & Payroll Year</b> must be between {frappe.bold(start_date)} and {frappe.bold(end_date)}."
            )

    def on_update(self):
        self.validate_and_set_challan_details_in_form_24q()

    def validate_and_set_challan_details_in_form_24q(self):
        if not self.payroll_month or not self.payroll_period:
            frappe.throw("Payroll Month and Payroll Period are required.")

        payroll_month = self.payroll_month.title()

        quarter_field = None
        for months, field in self.QUARTER_MAPPING.items():
            if payroll_month in months:
                quarter_field = field
                break

        if not quarter_field:
            frappe.throw(f"Invalid payroll_month: {payroll_month}")

        self.quarter = quarter_field

        try:
            form_24q_list = frappe.get_all(
                "Form 24Q",
                filters={"payroll_period": self.payroll_period},
                fields=["name"],
                limit=1,
            )

            if not form_24q_list:
                frappe.msgprint(
                    f"No Form 24Q found for payroll period: {self.payroll_period}",
                    title="Warning",
                )
                return

            docname = form_24q_list[0].name
            doc = frappe.get_doc("Form 24Q", docname)

            if not hasattr(doc, quarter_field):
                frappe.msgprint(
                    f"Quarter field {quarter_field} not found in Form 24Q document {docname}.",
                    title="Error",
                )
                return

            quarter_table = getattr(doc, quarter_field)

            monthly_income_tax = self.get_tax_deducted_from_employees(payroll_month, self.payroll_year)
            difference = 0
            if monthly_income_tax:
                difference = self.total_challan_amount - monthly_income_tax
            else:
                monthly_income_tax = 0

            month_exists = False
            for row in quarter_table:
                if row.month == payroll_month:
                    row.year = self.payroll_year
                    row.challan_amount_remitted = self.total_challan_amount
                    row.tax_deducted_from_employees = monthly_income_tax
                    row.difference = difference
                    row.challan_reference = self.name
                    month_exists = True
                    break

            if not month_exists:
                doc.append(
                    quarter_field,
                    {
                        "month": payroll_month,
                        "year": self.payroll_year,
                        "challan_amount_remitted": self.total_challan_amount,
                        "tax_deducted_from_employees": monthly_income_tax,
                        "difference": difference,
                        "challan_reference": self.name,
                    },
                )

            doc.save()
            frappe.msgprint(
                f"Updated Form 24Q ({docname}) with {payroll_month} in {quarter_field}.",
                title="Success",
            )

        except Exception as e:
            frappe.throw(f"Failed to update Form 24Q.")

    def get_tax_deducted_from_employees(self, payroll_month, payroll_year):
        month_number = datetime.strptime(payroll_month, "%b").month
        
        start_date = datetime(payroll_year, month_number, 1)
        end_date = start_date + relativedelta(months=1, days=-1)

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        salary_slips = frappe.get_all(
            "Salary Slip",
            filters={
                "payroll_frequency": "Monthly",
                "start_date": ["<=", end_date_str],
                "end_date": [">=", start_date_str],
                "current_month_income_tax": [">", 0],
            },
            fields=["name", "employee", "current_month_income_tax"],
        )

        total_tax = sum(
            slip.get("current_month_income_tax", 0) for slip in salary_slips
        )

        return round(total_tax)


