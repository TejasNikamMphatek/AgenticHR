# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DocumentCenter(Document):
    pass


@frappe.whitelist(allow_guest=True)
def force_download(docname):
    doc = frappe.get_doc("Document Center", docname)
    if not doc.document:
        frappe.throw("No document attached!")

    file_doc = frappe.get_doc("File", {"file_url": doc.document})

    frappe.local.response.filename = file_doc.file_name
    frappe.local.response.filecontent = file_doc.get_content()
    frappe.local.response.type = "download"
