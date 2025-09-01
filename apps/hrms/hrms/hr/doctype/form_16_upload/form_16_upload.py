# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import zipfile
import subprocess
import os, re

from frappe.model.document import Document
from frappe.utils.file_manager import get_file
# from pyhanko.sign import signers
# from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
# from pyhanko.sign.fields import SigFieldSpec
# print("PyHanko is available in Frappe!")

class Form16Upload(Document):

    def validate(self):
        # Restrict Upload Part A
        if self.upload_part_a and not self.upload_part_a.endswith(".zip"):
            frappe.throw("Only .zip files are allowed for Upload Part A")
        
        # Restrict Upload Part B
        if self.upload_part_b and not self.upload_part_b.endswith(".zip"):
            frappe.throw("Only .zip files are allowed for Upload Part B")


    def extract_zip(self, file_url, part_name):
        try:
            # Get File doctype record
            file_doc = frappe.get_doc("File", {"file_url": file_url})
            file_path = file_doc.get_full_path()

            # Normalize absolute path
            file_path = os.path.abspath(file_path)

            # If file not found, try alternative paths
            if not os.path.exists(file_path):
                alt_private = frappe.get_site_path("private", "files", os.path.basename(file_url))
                alt_public = frappe.get_site_path("public", "files", os.path.basename(file_url))

                if os.path.exists(alt_private):
                    file_path = alt_private
                elif os.path.exists(alt_public):
                    file_path = alt_public
                else:
                    frappe.throw(f"❌ File not found in private or public files: {file_url}")

            # Extract target directory
            extract_dir = frappe.get_site_path("private", "files", f"{self.name}_{part_name}")
            os.makedirs(extract_dir, exist_ok=True)

            # Open and test zip integrity
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                bad_file = zip_ref.testzip()
                if bad_file:
                    frappe.throw(f"❌ Corrupt file found inside ZIP: {bad_file}")

                zip_ref.extractall(extract_dir)

            frappe.msgprint(f"✅ {part_name} extracted successfully to: {extract_dir}")
            return extract_dir

        except zipfile.BadZipFile:
            frappe.throw("❌ The uploaded file is not a valid ZIP archive")

        except PermissionError as e:
            frappe.throw(f"❌ Permission denied: {str(e)}")

        except Exception as e:
            frappe.throw(f"❌ Unexpected error while extracting {part_name}: {str(e)}")


    def apply_digital_signature_external(self, part_name=None):

        # 1️⃣ Get active digital signature
        try:
            sign_conf = frappe.get_doc("Upload Digital Sign", {"is_active": 1})
        except frappe.DoesNotExistError:
            frappe.throw("No active Digital Signature configuration found.")

        if not sign_conf.digital_signature_file:
            frappe.throw("Digital Signature file not attached.")

        # 2️⃣ Paths
        base_dir = frappe.get_site_path("private", "files", f"{self.name}_{part_name}")
        if not os.path.isdir(base_dir):
            frappe.throw(f"Extracted directory not found for {part_name}: {base_dir}")

        signed_dir = os.path.join(base_dir, "signed")
        os.makedirs(signed_dir, exist_ok=True)

        # 3️⃣ Certificate file
        cert_doc = frappe.get_doc("File", {"file_url": sign_conf.digital_signature_file})
        cert_path = cert_doc.get_full_path()
        if not os.path.isfile(cert_path):
            frappe.throw(f"Certificate file does not exist: {cert_path}")

        # 4️⃣ Password
        cert_pass = getattr(sign_conf, "private_key_password", "mphatek@123")

        # 5️⃣ Sign PDFs
        signed_files = []
        skipped_files = []

        # for root, dirs, files in os.walk(base_dir):
        #     for fn in files:
        #         if fn.lower().endswith(".pdf"):
        #             input_pdf = os.path.join(root, fn)
        #             output_pdf = os.path.join(signed_dir, fn)
                    
        #             python_path = sys.executable
        #             pyhanko_path = os.path.join(os.path.dirname(python_path), "pyhanko")

        #             cmd = [
		# 				"pyhanko",  # Direct command
		# 				"sign",
		# 				"addsig", 
		# 				"--field", "Signature1",
		# 				"--signer", f"pemder:{cert_path}",
		# 				"--reason", "Form-16 Part A Signing",
		# 				"--out", output_pdf,
		# 				input_pdf,
		# 			]

        #             if cert_pass:
        #                 cmd.extend(["--key-passphrase", cert_pass])

        #             try:
        #                 subprocess.run(cmd, check=True, capture_output=True, text=True)
        #                 signed_files.append(output_pdf)
        #             except subprocess.CalledProcessError as e:
        #                 skipped_files.append(fn)
        #                 frappe.throw(f"Failed to sign {fn}, skipping...\nError: {e.stderr or e.stdout or str(e)}")
        #             except Exception as e:
        #                 skipped_files.append(fn)
        #                 frappe.throw(f"Unexpected error for {fn}: {str(e)}")

        if not signed_files:
            frappe.throw("No PDFs were signed.")

        frappe.msgprint(f"✅ Signed {len(signed_files)} PDF(s).")
        return signed_files

    def list_extracted_files(self, part_name):
        base_dir = frappe.get_site_path("private", "files", f"{self.name}_{part_name}")
        if not os.path.isdir(base_dir):
            frappe.throw(f"Extracted directory not found for {part_name}: {base_dir}")

        pdfs = []
        for root, dirs, files in os.walk(base_dir):
            if "__MACOSX" in root:
                continue
            for fn in files:
                if fn.lower().endswith(".pdf"):
                    rel_path = os.path.relpath(os.path.join(root, fn), base_dir)
                    pdfs.append(rel_path)

        return sorted(set(pdfs))



            
@frappe.whitelist()
def extract_part_a(docname):
    doc = frappe.get_doc("Form-16-Upload", docname)
    if not doc.upload_part_a:
        frappe.throw("Please upload Part A zip first")
        
    doc.extract_zip(doc.upload_part_a, "PartA")
    return "Part A Extracted Successfully"


@frappe.whitelist()
def extract_part_b(docname):
    doc = frappe.get_doc("Form-16-Upload", docname)
    if not doc.upload_part_b:
        frappe.throw("Please upload Part B zip first")
    doc.extract_zip(doc.upload_part_b, "PartB")
    return "Part B Extracted Successfully"


@frappe.whitelist()
def get_extracted_file_list(docname, part_name):
    doc = frappe.get_doc("Form-16-Upload", docname)
    return doc.list_extracted_files(part_name)



@frappe.whitelist()
def apply_digital_signature_part_a(docname):
    doc = frappe.get_doc("Form-16-Upload", docname)
    return doc.apply_digital_signature_external("PartA")


PAN_RE = re.compile(r'([A-Za-z]{5}[0-9]{4}[A-Za-z])')

def _extract_pan(name: str) -> str | None:
    m = PAN_RE.search(name)
    return m.group(1).upper() if m else None

@frappe.whitelist()
def publish_part_a(docname, part_name):
    doc = frappe.get_doc("Form-16-Upload", docname)
    doc_list = doc.list_extracted_files(part_name) 

    base_dir = frappe.get_site_path("private", "files", f"{doc.name}_{part_name}")
    # print(f"base_dir ==== {base_dir}")

    # Build items = [{rel_path, filename, pan}] and collect unique PANs
    items, unique_pans = [], set()
    for rel_path in doc_list:
        filename = os.path.basename(rel_path)
        pan = _extract_pan(filename)
        if pan:
            items.append({"rel_path": rel_path, "filename": filename, "pan": pan})
            unique_pans.add(pan)

    # print(unique_pans)
    if not items:
        frappe.throw("No PDFs with valid PAN in filename were found.")

    # Fetch employees mapped by PAN (case-insensitive, but we uppercase)
    employees = frappe.db.get_all(
        "Employee",
        filters={"pan_number": ["in", list(unique_pans)]},
        fields=["name", "employee_name", "pan_number"]
    )
    emp_map = {e["pan_number"].upper(): e for e in employees}
    # print("Matched Employees:", emp_map)

    created_docs, missing = [], []
    for it in items:
        employee = emp_map.get(it["pan"])
        if not employee:
            missing.append(it["pan"])
            continue

        pdf_path = os.path.abspath(os.path.join(base_dir, it["rel_path"]))
        if not os.path.exists(pdf_path):
            frappe.throw(f"PDF not found: {pdf_path}")
            continue

        # print(f"Attaching PDF: {pdf_path} -> Employee: {employee['name']}")

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": it["filename"],
            "attached_to_doctype": "Employee",
            "attached_to_name": employee["name"],
            "is_private": 1,
            "content": open(pdf_path, "rb").read(),
            "decode": False
        })
        file_doc.insert(ignore_permissions=True)

        doc_center = frappe.get_doc({
            "doctype": "Document Center",
            "employee": employee["name"],
            "document_type": "Form-16-Upload",
            "document_name": it["filename"],
            "document": file_doc.file_url
        })
        doc_center.insert(ignore_permissions=True)
        created_docs.append(doc_center.name)

    frappe.db.commit()

    return {
        "status": "success",
        "created_records": created_docs,
        "matched_employees": employees,
        "missing_pans": sorted(set(missing)),
        "processed_files": [it["filename"] for it in items]
    }


@frappe.whitelist()
def publish_part_b(docname, part_name):
    doc = frappe.get_doc("Form-16-Upload", docname)
    doc_list = doc.list_extracted_files(part_name) 

    base_dir = frappe.get_site_path("private", "files", f"{doc.name}_{part_name}")
    # print(f"base_dir ==== {base_dir}")

    # Build items = [{rel_path, filename, pan}] and collect unique PANs
    items, unique_pans = [], set()
    for rel_path in doc_list:
        filename = os.path.basename(rel_path)
        pan = _extract_pan(filename)
        if pan:
            items.append({"rel_path": rel_path, "filename": filename, "pan": pan})
            unique_pans.add(pan)

    # print(unique_pans)
    if not items:
        frappe.throw("No PDFs with valid PAN in filename were found.")

    # Fetch employees mapped by PAN (case-insensitive, but we uppercase)
    employees = frappe.db.get_all(
        "Employee",
        filters={"pan_number": ["in", list(unique_pans)]},
        fields=["name", "employee_name", "pan_number"]
    )
    emp_map = {e["pan_number"].upper(): e for e in employees}
    # print("Matched Employees:", emp_map)

    created_docs, missing = [], []
    for it in items:
        employee = emp_map.get(it["pan"])
        if not employee:
            missing.append(it["pan"])
            continue

        pdf_path = os.path.abspath(os.path.join(base_dir, it["rel_path"]))
        if not os.path.exists(pdf_path):
            frappe.throw(f"PDF not found: {pdf_path}")
            continue

        # print(f"Attaching PDF: {pdf_path} -> Employee: {employee['name']}")

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": it["filename"],
            "attached_to_doctype": "Employee",
            "attached_to_name": employee["name"],
            "is_private": 1,
            "content": open(pdf_path, "rb").read(),
            "decode": False
        })
        file_doc.insert(ignore_permissions=True)

        doc_center = frappe.get_doc({
            "doctype": "Document Center",
            "employee": employee["name"],
            "document_type": "Form-16-Upload",
            "document_name": it["filename"],
            "document": file_doc.file_url
        })
        doc_center.insert(ignore_permissions=True)
        created_docs.append(doc_center.name)

    frappe.db.commit()

    return {
        "status": "success",
        "created_records": created_docs,
        "matched_employees": employees,
        "missing_pans": sorted(set(missing)),
        "processed_files": [it["filename"] for it in items]
    }
