import math

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, get_link_to_form, month_diff

from hrms.hr.utils import get_salary_assignments
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip


def calculate_annual_eligible_hra_exemption(doc):
	basic_component, hra_component = frappe.db.get_value(
		"Company", doc.company, ["basic_component", "hra_component"]
	)

	if not (basic_component and hra_component):
		frappe.throw(
			_("Please set Basic and HRA component in Company {0}").format(
				get_link_to_form("Company", doc.company)
			)
		)

	annual_exemption = monthly_exemption = hra_amount = basic_amount = da_amount = 0

	if hra_component and basic_component:
		assignments = get_salary_assignments(doc.employee, doc.payroll_period)
		print(assignments[0]['from_date'])

		if not assignments and doc.docstatus == 1:
			frappe.throw(_("Salary Structure must be submitted before submission of {0}").format(doc.doctype))

		assignment_dates = [assignment.from_date for assignment in assignments]

		for idx, assignment in enumerate(assignments):
			if has_hra_component(assignment.salary_structure, hra_component):
				basic_salary_amt, hra_salary_amt = get_component_amt_from_salary_slip(
					doc.employee,
					assignment.salary_structure,
					basic_component,
					hra_component,
					assignment.from_date,
				)
				to_date = get_end_date_for_assignment(assignment_dates, idx, doc.payroll_period)

				frequency = frappe.get_value(
					"Salary Structure", assignment.salary_structure, "payroll_frequency"
				)
				print("assignment.from_date = ",assignment.from_date)
				print("to_date = ",to_date)
				basic_amount += get_component_pay(frequency, basic_salary_amt, assignment.from_date, to_date) 
				hra_amount += get_component_pay(frequency, hra_salary_amt, assignment.from_date, to_date)
	    
		

		if hra_amount:
			if doc.monthly_house_rent:
				# annual_exemption = calculate_hra_exemption(
				# 	assignment.salary_structure,
				# 	basic_amount,
				# 	hra_amount,
				# 	doc.monthly_house_rent,
				# 	doc.rented_in_metro_city,
				# 	assignment.from_date,
				# 	to_date
				# )

				annual_exemption = calculate_hra_exemption(
					assignment.salary_structure,
					basic_salary_amt,
					hra_salary_amt,
					doc.monthly_house_rent,
					doc.rented_in_metro_city,
					assignment.from_date,
					to_date
				)
				if annual_exemption > 0:
					total_months = month_diff(to_date, assignment.from_date)
					monthly_exemption = annual_exemption / total_months
				else:
					annual_exemption = 0

	return frappe._dict(
		{
			"hra_amount": hra_amount,
			"annual_exemption": annual_exemption,
			"monthly_exemption": monthly_exemption,
		}
	)


def has_hra_component(salary_structure, hra_component):
	return frappe.db.exists(
		"Salary Detail",
		{
			"parent": salary_structure,
			"salary_component": hra_component,
			"parentfield": "earnings",
			"parenttype": "Salary Structure",
		},
	)


def get_end_date_for_assignment(assignment_dates, idx, payroll_period):
	end_date = None

	try:
		end_date = assignment_dates[idx + 1]
		end_date = add_days(end_date, -1)
	except IndexError:
		pass

	if not end_date:
		end_date = frappe.db.get_value("Payroll Period", payroll_period, "end_date")

	return end_date


def get_component_amt_from_salary_slip(employee, salary_structure, basic_component, hra_component, from_date):
	salary_slip = make_salary_slip(
		salary_structure,
		employee=employee,
		for_preview=1,
		ignore_permissions=True,
		posting_date=from_date,
	)

	basic_amt, hra_amt, da_amt= 0, 0, 0
	for earning in salary_slip.earnings:
		if earning.salary_component == basic_component:
			basic_amt = earning.amount
		elif earning.salary_component == hra_component:
			hra_amt = earning.amount
		if basic_amt and hra_amt:
			return basic_amt, hra_amt
	return basic_amt, hra_amt


def calculate_hra_exemption(
	salary_structure, monthly_basic_pay, monthly_hra_pay, monthly_house_rent, rented_in_metro_city, from_date, to_date
):
	# TODO make this configurable
	exemptions = []
	# case 1: The actual amount allotted by the employer as the HRA.
	total_months = month_diff(to_date, from_date)
	exemptions.append(monthly_hra_pay * total_months)
	print(monthly_hra_pay,"monthly_hra_pay")
	# print("total_months",total_months)
	# case 2: Actual rent paid less 10% of the basic salary.
	######################################################
	monthly_da = monthly_basic_pay * 0.4
	basic_da_monthly = monthly_basic_pay + monthly_da
	exemptions.append((monthly_house_rent-(basic_da_monthly * 0.1)) * total_months)

	# print(basic_da_monthly)

	# case 3: 50% of the basic salary, if the employee is staying in a metro city (40% for a non-metro city).
	annual_basic_da = basic_da_monthly * total_months
	exemptions.append(annual_basic_da * 0.5 if rented_in_metro_city else annual_basic_da * 0.4)
	print((exemptions))
	
	# return minimum of 3 cases
	return min(exemptions)


def get_component_pay(frequency, amount, from_date, to_date):
	days = date_diff(to_date, from_date) + 1

	if frequency == "Daily":
		return amount * days
	elif frequency == "Weekly":
		return amount * math.floor(days / 7)
	elif frequency == "Fortnightly":
		return amount * math.floor(days / 14)
	elif frequency == "Monthly":
		return amount * month_diff(to_date, from_date)
	elif frequency == "Bimonthly":
		return amount * (month_diff(to_date, from_date) / 2)


def validate_house_rent_dates(doc):
	if not doc.rented_to_date or not doc.rented_from_date:
		frappe.throw(_("House rented dates required for exemption calculation"))

	if date_diff(doc.rented_to_date, doc.rented_from_date) < 14:
		frappe.throw(_("House rented dates should be atleast 15 days apart"))

	proofs = frappe.db.sql(
		"""
		select name
		from `tabEmployee Tax Exemption Proof Submission`
		where
			docstatus=1 and employee=%(employee)s and payroll_period=%(payroll_period)s
			and (rented_from_date between %(from_date)s and %(to_date)s or rented_to_date between %(from_date)s and %(to_date)s)
	""",
		{
			"employee": doc.employee,
			"payroll_period": doc.payroll_period,
			"from_date": doc.rented_from_date,
			"to_date": doc.rented_to_date,
		},
	)

	if proofs:
		frappe.throw(_("House rent paid days overlapping with {0}").format(proofs[0][0]))


def calculate_hra_exemption_for_period(doc):
	monthly_rent, eligible_hra = 0, 0
	if doc.house_rent_payment_amount:
		validate_house_rent_dates(doc)
		# TODO receive rented months or validate dates are start and end of months?
		# Calc monthly rent, round to nearest .5
		# factor = flt(date_diff(doc.rented_to_date, doc.rented_from_date) + 1) / 30
		factor = flt(month_diff(doc.rented_to_date, doc.rented_from_date))
		# print(doc.rented_to_date)
		# print(doc.rented_from_date)

		# factor = round(factor * 2) / 2
		# print("factor",factor)
		monthly_rent = doc.house_rent_payment_amount / factor
		
		# update field used by calculate_annual_eligible_hra_exemption
		doc.monthly_house_rent = monthly_rent
		exemptions = calculate_annual_eligible_hra_exemption(doc)

		if exemptions["monthly_exemption"]:
			# calc total exemption amount
			eligible_hra = exemptions["monthly_exemption"] * factor
		exemptions["monthly_house_rent"] = monthly_rent
		exemptions["total_eligible_hra_exemption"] = eligible_hra
		return exemptions
