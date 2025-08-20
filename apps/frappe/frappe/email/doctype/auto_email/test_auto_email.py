# Copyright (c) 2025,  Pipal ERP and Contributors
# License: MIT. See LICENSE
import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, get_link_to_form, today
from frappe.utils.data import is_html

# test_records = frappe.get_test_records('Auto Email Report')


class TestAutoEmail(FrappeTestCase):
	def test_auto_email(self):
		frappe.delete_doc("Auto Email Report", "Permitted Documents For User")

		auto_email = get_auto_email()

		data = auto_email.get_report_content()

		self.assertTrue(is_html(data))
		self.assertTrue(str(get_link_to_form("Module Def", "Core")) in data)

		auto_email.format = "CSV"

		data = auto_email.get_report_content()
		self.assertTrue('"Language","Core"' in data)

		auto_email.format = "XLSX"

		data = auto_email.get_report_content()

	def test_dynamic_date_filters(self):
		auto_email = get_auto_email()

		auto_email.dynamic_date_period = "Weekly"
		auto_email.from_date_field = "from_date"
		auto_email.to_date_field = "to_date"

		auto_email.prepare_dynamic_filters()

		self.assertEqual(auto_email.filters["from_date"], add_to_date(today(), weeks=-1))
		self.assertEqual(auto_email.filters["to_date"], today())


def get_auto_email():
	if not frappe.db.exists("Auto Email Report", "Permitted Documents For User"):
		auto_email = frappe.get_doc(
			dict(
				doctype="Auto Email Report",
				report="Permitted Documents For User",
				report_type="Script Report",
				user="Administrator",
				enabled=1,
				email_to="test@example.com",
				format="HTML",
				frequency="Daily",
				filters=json.dumps(dict(user="Administrator", doctype="DocType")),
			)
		).insert()
	else:
		auto_email = frappe.get_doc("Auto Email Report", "Permitted Documents For User")

	return auto_email
