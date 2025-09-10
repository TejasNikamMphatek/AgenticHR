# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import zipfile
import subprocess
import os, re

from frappe.model.document import Document


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
        dg_sign_info = frappe.get_single("Upload Digital Sign")

        signer_name = dg_sign_info.get("signer_name")
        signer_designation = dg_sign_info.get("signer_designation")
        location = dg_sign_info.get("location")


        if not os.path.isfile(cert_path):
            frappe.throw(f"Certificate file does not exist: {cert_path}")

        # 4️⃣ Password
        cert_pass = getattr(sign_conf, "private_key_password", "mphatek@123")

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith('.pdf') and 'signed' not in root:
                    input_pdf = os.path.join(root, file)
                    output_pdf = os.path.join(signed_dir, file)
                    
                    cmd = [
                        "python3", frappe.get_site_path("sign_pdfs.py"), 
                        input_pdf, output_pdf, cert_path, cert_pass,
                        signer_name or "Digital Signer",
                        signer_designation or "Authorized Signatory", 
                        location or "PUNE",
                        part_name  # Pass the part_name to determine signing method
                    ]

                    try:
                        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                        # frappe.msgprint(f"Successfully signed {file} for {part_name}")
                    except subprocess.CalledProcessError as e:
                        # print(f"Error signing {file}: {e.stderr}")
                        frappe.throw(f"Failed to sign {file}")

        return f"Digital signatures applied to {part_name}"



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

@frappe.whitelist()
def apply_digital_signature_part_b(docname):
    doc = frappe.get_doc("Form-16-Upload", docname)
    return doc.apply_digital_signature_external("PartB")

PAN_RE = re.compile(r'([A-Za-z]{5}[0-9]{4}[A-Za-z])')

def _extract_pan(name: str) -> str | None:
    m = PAN_RE.search(name)
    return m.group(1).upper() if m else None

@frappe.whitelist()
def publish_part_a(docname, part_name):
    doc = frappe.get_doc("Form-16-Upload", docname)
    
    # Path to signed folder - use absolute path
    base_dir = os.path.abspath(frappe.get_site_path("private", "files", f"{doc.name}_{part_name}", "signed"))
    
    # print(f"Looking for signed files in: {base_dir}")
    
    if not os.path.exists(base_dir):
        frappe.throw(f"Signed directory not found: {base_dir}")
    
    # Collect signed PDFs
    signed_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.pdf')]
    
    # print(f"Found {len(signed_files)} PDF files: {signed_files}")
    
    if not signed_files:
        frappe.throw("No PDF files found in signed folder")
    
    items, unique_pans = [], set()
    for filename in signed_files:
        pan = _extract_pan(filename)
        if pan:
            items.append({"rel_path": filename, "filename": filename, "pan": pan})
            unique_pans.add(pan)

    if not items:
        frappe.throw("No PDFs with valid PAN in filename were found in signed folder.")

    # print(f"unique_pans = {unique_pans}")
    
    # Employees mapped by PAN
    employees = frappe.db.get_all(
        "Employee",
        filters={"pan_number": ["in", list(unique_pans)]},
        fields=["name", "employee_name", "pan_number"]
    )
    emp_map = {e["pan_number"].upper(): e for e in employees}

    # print(f"employee length :::: {len(emp_map)}")

    created_docs, missing = [], []
    for it in items:
        employee = emp_map.get(it["pan"])
        if not employee:
            missing.append(it["pan"])
            continue

        pdf_path = os.path.join(base_dir, it["filename"])
        # print(f"Processing file: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            # print(f"File not found: {pdf_path}")
            continue

        # --- Check for existing file and validate it
        existing_files = frappe.db.get_all(
            "File", 
            filters={
                "file_name": it["filename"], 
                "attached_to_doctype": "Employee", 
                "attached_to_name": employee["name"]
            },
            fields=["name", "file_url"]
        )

        file_doc = None
        valid_existing_file = False
        
        # Check if any existing file actually exists on disk
        for existing in existing_files:
            try:
                temp_doc = frappe.get_doc("File", existing["name"])
                existing_path = temp_doc.get_full_path()
                if os.path.exists(existing_path):
                    file_doc = temp_doc
                    valid_existing_file = True
                    # print(f"Found valid existing file: {file_doc.file_url}")
                    break
                else:
                    frappe.msgprint(f"Existing file record found but file missing on disk: {existing_path}")
            except Exception as e:
                frappe.log_error(f"Error checking existing file {existing['name']}: {str(e)}")
                continue
        
        # If no valid existing file found, create new one
        if not valid_existing_file:
            try:
                # Delete any broken file records first
                for existing in existing_files:
                    try:
                        frappe.delete_doc("File", existing["name"], force=1)
                        # print(f"Deleted broken file record: {existing['name']}")
                    except:
                        pass
                
                # Read file content
                with open(pdf_path, "rb") as f:
                    file_content = f.read()
                
                # print(f"Read {len(file_content)} bytes from {pdf_path}")
                
                # Create File document using proper method
                file_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": it["filename"],
                    "attached_to_doctype": "Employee",
                    "attached_to_name": employee["name"],
                    "is_private": 1,
                    "content": file_content,
                    "decode": False
                })
                file_doc.insert(ignore_permissions=True)
                
                # print(f"Created new file with URL: {file_doc.file_url}")
                
                # Verify the file was actually saved
                actual_path = file_doc.get_full_path()
                # print(f"File saved to: {actual_path}")
                
                if not os.path.exists(actual_path):
                    frappe.throw(f"Failed to save file {it['filename']} to disk at {actual_path}")
                
            except Exception as e:
                # print(f"Error creating file {it['filename']}: {str(e)}")
                frappe.log_error(f"File creation error for {it['filename']}: {str(e)}", "Form16Upload")
                continue

        # --- Document Center creation (skip if exists)
        existing_doc_center = frappe.db.exists("Document Center", {
            "employee": employee["name"], 
            "document_name": it["filename"]
        })
        
        if existing_doc_center:
            # Update existing document center with correct file URL
            doc_center = frappe.get_doc("Document Center", existing_doc_center)
            if doc_center.document != file_doc.file_url:
                doc_center.document = file_doc.file_url
                doc_center.save(ignore_permissions=True)
                # print(f"Updated Document Center entry: {doc_center.name} with new URL: {file_doc.file_url}")
            # else:
            #     frappe.msgprint(f"Document Center entry already exists with correct URL: {it['filename']}")
            continue

        try:
            doc_center = frappe.get_doc({
                "doctype": "Document Center",
                "employee": employee["name"],
                "document_type": "Form-16-Upload",
                "document_name": it["filename"],
                "document": file_doc.file_url
            })
            doc_center.insert(ignore_permissions=True)
            created_docs.append(doc_center.name)
            
            # print(f"Created Document Center entry: {doc_center.name} with document URL: {file_doc.file_url}")
            
        except Exception as e:
            # print(f"Error creating Document Center entry: {str(e)}")
            frappe.log_error(f"Document Center creation error: {str(e)}", "Form16Upload")

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
    
    # Path to signed folder - use absolute path
    base_dir = os.path.abspath(frappe.get_site_path("private", "files", f"{doc.name}_{part_name}", "signed"))
    
    # print(f"Looking for signed files in: {base_dir}")
    
    if not os.path.exists(base_dir):
        frappe.throw(f"Signed directory not found: {base_dir}")
    
    # Collect signed PDFs
    signed_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.pdf')]
    
    # print(f"Found {len(signed_files)} PDF files: {signed_files}")
    
    if not signed_files:
        frappe.throw("No PDF files found in signed folder")
    
    items, unique_pans = [], set()
    for filename in signed_files:
        pan = _extract_pan(filename)
        if pan:
            items.append({"rel_path": filename, "filename": filename, "pan": pan})
            unique_pans.add(pan)

    if not items:
        frappe.throw("No PDFs with valid PAN in filename were found in signed folder.")

    # print(f"unique_pans = {unique_pans}")
    
    # Employees mapped by PAN
    employees = frappe.db.get_all(
        "Employee",
        filters={"pan_number": ["in", list(unique_pans)]},
        fields=["name", "employee_name", "pan_number"]
    )
    emp_map = {e["pan_number"].upper(): e for e in employees}

    # print(f"employee length :::: {len(emp_map)}")

    created_docs, missing, skipped_files = [], [], []
    for it in items:
        employee = emp_map.get(it["pan"])
        if not employee:
            missing.append(it["pan"])
            continue

        pdf_path = os.path.join(base_dir, it["filename"])
        # print(f"Processing file: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            # print(f"File not found: {pdf_path}")
            continue

        # --- Check for existing file and validate it
        existing_files = frappe.db.get_all(
            "File", 
            filters={
                "file_name": it["filename"], 
                "attached_to_doctype": "Employee", 
                "attached_to_name": employee["name"]
            },
            fields=["name", "file_url"]
        )

        file_doc = None
        valid_existing_file = False
        
        # Check if any existing file actually exists on disk
        for existing in existing_files:
            try:
                temp_doc = frappe.get_doc("File", existing["name"])
                existing_path = temp_doc.get_full_path()
                if os.path.exists(existing_path):
                    file_doc = temp_doc
                    valid_existing_file = True
                    # print(f"Found valid existing file: {file_doc.file_url}")
                    break
                else:
                    frappe.msgprint(f"Existing file record found but file missing on disk: {existing_path}")
            except Exception as e:
                frappe.log_error(f"Error checking existing file {existing['name']}: {str(e)}")
                continue
        
        # If no valid existing file found, create new one
        if not valid_existing_file:
            try:
                # Delete any broken file records first
                for existing in existing_files:
                    try:
                        frappe.delete_doc("File", existing["name"], force=1)
                        # print(f"Deleted broken file record: {existing['name']}")
                    except:
                        pass
                
                # Read file content
                with open(pdf_path, "rb") as f:
                    file_content = f.read()
                
                # print(f"Read {len(file_content)} bytes from {pdf_path}")
                
                # Create File document using proper method
                file_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": it["filename"],
                    "attached_to_doctype": "Employee",
                    "attached_to_name": employee["name"],
                    "is_private": 1,
                    "content": file_content,
                    "decode": False
                })
                file_doc.insert(ignore_permissions=True)
                
                # print(f"Created new file with URL: {file_doc.file_url}")
                
                # Verify the file was actually saved
                actual_path = file_doc.get_full_path()
                # print(f"File saved to: {actual_path}")
                
                if not os.path.exists(actual_path):
                    frappe.throw(f"Failed to save file {it['filename']} to disk at {actual_path}")
                
            except Exception as e:
                # print(f"Error creating file {it['filename']}: {str(e)}")
                frappe.log_error(f"File creation error for {it['filename']}: {str(e)}", "Form16Upload")
                continue

        # --- Document Center creation (skip if exists)
        existing_doc_center = frappe.db.exists("Document Center", {
            "employee": employee["name"], 
            "document_name": it["filename"]
        })
        
        if existing_doc_center:
            # Update existing document center with correct file URL
            doc_center = frappe.get_doc("Document Center", existing_doc_center)
            if doc_center.document != file_doc.file_url:
                doc_center.document = file_doc.file_url
                doc_center.save(ignore_permissions=True)
                # print(f"Updated Document Center entry: {doc_center.name} with new URL: {file_doc.file_url}")
            # else:
                # frappe.msgprint(f"Document Center entry already exists with correct URL: {it['filename']}")
            skipped_files.append(it["filename"])
            continue

        try:
            doc_center = frappe.get_doc({
                "doctype": "Document Center",
                "employee": employee["name"],
                "document_type": "Form-16-Upload",
                "document_name": it["filename"],
                "document": file_doc.file_url
            })
            doc_center.insert(ignore_permissions=True)
            created_docs.append(doc_center.name)
            
            # print(f"Created Document Center entry: {doc_center.name} with document URL: {file_doc.file_url}")
            
        except Exception as e:
            # print(f"Error creating Document Center entry: {str(e)}")
            frappe.log_error(f"Document Center creation error: {str(e)}", "Form16Upload")

    frappe.db.commit()

    return {
        "status": "success",
        "created_records": created_docs,
        "matched_employees": employees,
        "missing_pans": sorted(set(missing)),
        "skipped_files": skipped_files,
        "processed_files": [it["filename"] for it in items]
    }

