# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document
from frappe.utils import flt
import frappe

from hrms.hr.utils import (
	calculate_hra_exemption_for_period,
	get_total_exemption_amount,
	validate_active_employee,
	validate_duplicate_exemption_for_payroll_period,
	validate_tax_declaration,
)

class EmployeeTaxExemptionProofSubmission(Document):
	def validate(self):
		validate_active_employee(self.employee)
		validate_tax_declaration(self.tax_exemption_proofs)
		self.set_total_actual_amount()
		self.set_total_exemption_amount()
		self.calculate_hra_exemption()
		validate_duplicate_exemption_for_payroll_period(
			self.doctype, self.name, self.payroll_period, self.employee
		)



	def set_total_actual_amount(self):
		# new_regime_exempt_amount = 0
		# print("total_actual_amount",self.total_actual_amount)
		income_tax_slab = frappe.db.get_value(
				"Salary Structure Assignment",
				{"employee": self.employee, "docstatus": 1},
				"income_tax_slab",
				cache=True,
		)

		self.is_new_regime = frappe.db.get_value(
			"Income Tax Slab",
				{"name": income_tax_slab, "docstatus": 1,"disabled":0},
				"is_new_regime",
				cache=True,
		)
		if self.is_new_regime :
			self.total_actual_amount = 0
		elif not self.is_new_regime :
			self.total_actual_amount = flt(self.get("house_rent_payment_amount"))
		

		# print("self.total_actual_amount case 1", self.total_actual_amount)

		for d in self.tax_exemption_proofs :
			if self.is_new_regime and d.is_exempt_allowed:
				self.total_actual_amount += flt(d.amount)
			elif (self.is_new_regime) and (not d.is_exempt_allowed):
				self.total_actual_amount += 0
			elif not self.is_new_regime :
				self.total_actual_amount += flt(d.amount)

		# print("total_actual_amount case 2",self.total_actual_amount)
		# print("is_new_regime",is_new_regime)
		# print("is_exempt_allowed",d.is_exempt_allowed)

	def set_total_exemption_amount(self):
		if self.is_new_regime :
			self.exemption_amount = flt(
				self.total_actual_amount
			)
		else :
			self.exemption_amount = flt(
				get_total_exemption_amount(self.tax_exemption_proofs), self.precision("exemption_amount")
			)
		

	def calculate_hra_exemption(self):
		self.monthly_hra_exemption, self.monthly_house_rent, self.total_eligible_hra_exemption = 0, 0, 0
		if self.get("house_rent_payment_amount") and (not self.is_new_regime):
			hra_exemption = calculate_hra_exemption_for_period(self)
			if hra_exemption:
				self.exemption_amount += hra_exemption["total_eligible_hra_exemption"]
				self.exemption_amount = flt(self.exemption_amount, self.precision("exemption_amount"))
				self.monthly_hra_exemption = flt(
					hra_exemption["monthly_exemption"], self.precision("monthly_hra_exemption")
				)
				self.monthly_house_rent = flt(
					hra_exemption["monthly_house_rent"], self.precision("monthly_house_rent")
				)
				self.total_eligible_hra_exemption = flt(
					hra_exemption["total_eligible_hra_exemption"],
					self.precision("total_eligible_hra_exemption"),
				)
