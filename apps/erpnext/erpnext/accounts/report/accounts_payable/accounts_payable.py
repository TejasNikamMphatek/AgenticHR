# Copyright (c) 2025,  Pipal ERP Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


def execute(filters=None):
	args = {
		"account_type": "Payable",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	return ReceivablePayableReport(filters).run(args)
