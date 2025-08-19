# Copyright (c) 2024, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Coalesce
from frappe.query_builder.terms import SubQuery
from frappe.utils import get_link_to_form

from hrms.hr.utils import validate_bulk_tool_fields
from hrms.payroll.doctype.salary_structure.salary_structure import (
	create_salary_structure_assignment,
)


class BulkSalaryStructureAssignment(Document):
	@frappe.whitelist()
	def get_employees(self, advanced_filters: list) -> list:
		quick_filter_fields = [
			"company",
			"employment_type",
			"branch",
			"department",
			"designation",
			"grade",
		]
		filters = [[d, "=", self.get(d)] for d in quick_filter_fields if self.get(d)]
		filters += advanced_filters

		Assignment = frappe.qb.DocType("Salary Structure Assignment")
		employees_with_assignments = SubQuery(
			frappe.qb.from_(Assignment)
			.select(Assignment.employee)
			.distinct()
			.where((Assignment.from_date == self.from_date) & (Assignment.docstatus == 1))
		)
		already_assigned_salary_structure = frappe.db.get_all(
			"Salary Structure Assignment",
			filters={"docstatus": 1},
			fields=["employee"]
		)
		already_assigned_ids = {d["employee"] for d in already_assigned_salary_structure}

		# QB query
		Employee = frappe.qb.DocType("Employee")
		query = (
			frappe.qb.get_query(
				Employee,
				fields=[
					Employee.employee, 
					Employee.employee_name, 
					Employee.ctc.as_("base"),
					# Add a default value for variable if not present
					ConstantColumn(0).as_("variable")
				],
				filters=filters,
			)
			.where(
				(Employee.status == "Active")
				& (Employee.date_of_joining <= self.from_date)
				& ((Employee.relieving_date > self.from_date) | (Employee.relieving_date.isnull()))
			)
		)

		filtered_employee = query.run(as_dict=True)

		# Now filter out employees already assigned
		filtered_employee = [
			emp for emp in filtered_employee if emp["employee"] not in already_assigned_ids
		]

		# Ensure base and variable have default values
		for emp in filtered_employee:
			emp["base"] = emp.get("base") or 0
			emp["variable"] = emp.get("variable") or 0

		return filtered_employee

	@frappe.whitelist()
	def bulk_assign_structure(self, employees: list) -> None:
		mandatory_fields = ["salary_structure", "from_date", "company"]
		validate_bulk_tool_fields(self, mandatory_fields, employees)

		if len(employees) <= 30:
			return self._bulk_assign_structure(employees)

		frappe.enqueue(self._bulk_assign_structure, timeout=3000, employees=employees)
		frappe.msgprint(
			_("Creation of Salary Structure Assignments has been queued. It may take a few minutes."),
			alert=True,
			indicator="blue",
		)

	def _bulk_assign_structure(self, employees: list) -> None:
		success, failure = [], []
		count = 0
		savepoint = "before_salary_assignment"

		for d in employees:
			try:
				frappe.db.savepoint(savepoint)
				assignment = create_salary_structure_assignment(
					employee=d["employee"],
					salary_structure=self.salary_structure,
					company=self.company,
					currency=self.currency,
					payroll_payable_account=self.payroll_payable_account,
					from_date=self.from_date,
					base=d.get("base", 0),  # Use get() with default value
					variable=d.get("variable", 0),  # Use get() with default value
					income_tax_slab=self.income_tax_slab,
				)
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				frappe.log_error(
					f"Bulk Assignment - Salary Structure Assignment failed for employee {d['employee']}.",
					reference_doctype="Salary Structure Assignment",
				)
				failure.append(d["employee"])
			else:
				success.append(
					{
						"doc": get_link_to_form("Salary Structure Assignment", assignment),
						"employee": d["employee"],
					}
				)

			count += 1
			frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Structure..."))

		frappe.publish_realtime(
			"completed_bulk_salary_structure_assignment",
			message={"success": success, "failure": failure},
			doctype="Bulk Salary Structure Assignment",
			after_commit=True,
		)