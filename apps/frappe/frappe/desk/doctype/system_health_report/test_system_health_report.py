# Copyright (c) 2024, mPHATEK Systems and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSystemHealthReport(FrappeTestCase):
	def test_it_works(self):
		frappe.get_doc("System Health Report")
