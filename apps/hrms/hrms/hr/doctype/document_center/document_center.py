import frappe
import os
from frappe.model.document import Document
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature, ValidationContext
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

class DocumentCenter(Document):
    """Custom Document Center Doctype"""
    pass

# ------------------------------------
# ✅ Verify digital signature function
# ------------------------------------
@frappe.whitelist(allow_guest=False)
def verify_digital_signature(docname):
    doc = frappe.get_doc("Document Center", docname)
    if not doc.document:
        frappe.throw("No document attached for verification!")

    file_doc = frappe.get_doc("File", {"file_url": doc.document})
    file_name = os.path.basename(file_doc.file_url)

    # Resolve file path
    pdf_path = frappe.get_site_path("private", "files", file_name)
    if not os.path.exists(pdf_path):
        pdf_path = frappe.get_site_path("public", "files", file_name)
    if not os.path.exists(pdf_path):
        frappe.throw(f"File not found: {pdf_path}")

    try:
        with open(pdf_path, "rb") as f:
            reader = PdfFileReader(f)
            vc = ValidationContext(trust_roots=None)  # Allow self-signed certs
            signatures = reader.embedded_signatures

            if not signatures:
                doc.db_set("verification_status", "Invalid")
                doc.db_set("signature_verified", 0)
                frappe.throw("❌ No digital signatures found in the document.")

            valid_signature_found = False
            for sig in signatures:
                status = validate_pdf_signature(sig, vc)
                if status.intact:
                    valid_signature_found = True
                    break

            if valid_signature_found:
                doc.db_set("verification_status", "Verified")
                doc.db_set("signature_verified", 1)
                frappe.msgprint("✅ Digital signature verified successfully.")
                return {"status": "success", "message": "Digital signature verified successfully."}
            else:
                doc.db_set("verification_status", "Invalid")
                doc.db_set("signature_verified", 0)
                frappe.throw("❌ Invalid or untrusted digital signature.")

    except ImportError:
        frappe.throw("pyHanko is not installed on this system.")
    except Exception as e:
        frappe.throw(f"Verification failed: {str(e)}")
def overlay_verified_image(original_pdf, tick_image_path, output_pdf):
    reader = PdfReader(original_pdf)
    writer = PdfWriter()

    # Temporary PDF for the image stamp
    temp_stamp_path = frappe.get_site_path("private", "files", "temp_tick_stamp.pdf")
    width, height = letter
    c = canvas.Canvas(temp_stamp_path, pagesize=letter)

    # Load tick image
    img = ImageReader(tick_image_path)
    img_width, img_height = img.getSize()

    # Reduce size further (8% of original)
    scale = 0.08
    img_width *= scale
    img_height *= scale

    # Draw tick image at bottom-right, slightly lower
    c.drawImage(img, width - img_width - 20, 5, width=img_width, height=img_height, mask='auto')
    c.save()

    stamp_pdf = PdfReader(temp_stamp_path).pages[0]

    # Overlay stamp on all pages
    for page in reader.pages:
        page.merge_page(stamp_pdf)
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    os.remove(temp_stamp_path)
    return output_pdf
def overlay_verified_image(original_pdf, tick_image_path, output_pdf):
    reader = PdfReader(original_pdf)
    writer = PdfWriter()

    # Load tick image once
    img = ImageReader(tick_image_path)
    img_width, img_height = img.getSize()
    scale = 0.07  # 7% of original to make it smaller
    img_width *= scale
    img_height *= scale

    for i, page in enumerate(reader.pages):
        # Get page dimensions
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        # Temporary PDF canvas for this page
        temp_stamp_path = frappe.get_site_path("private", "files", f"temp_tick_stamp_{i}.pdf")
        c = canvas.Canvas(temp_stamp_path, pagesize=(page_width, page_height))

        # Draw tick smaller and lower (y=2)
        c.drawImage(img, page_width - img_width - 20, 2, width=img_width, height=img_height, mask='auto')
        c.save()

        # Merge stamp
        stamp_pdf = PdfReader(temp_stamp_path).pages[0]
        page.merge_page(stamp_pdf)
        writer.add_page(page)

        # Clean up temp
        os.remove(temp_stamp_path)

    # Write final PDF
    with open(output_pdf, "wb") as f:
        writer.write(f)

    return output_pdf

# def overlay_verified_image(original_pdf, tick_image_path, output_pdf):
#     reader = PdfReader(original_pdf)
#     writer = PdfWriter()

#     # Temporary PDF for the image stamp
#     temp_stamp_path = frappe.get_site_path("private", "files", "temp_tick_stamp.pdf")
#     width, height = letter
#     c = canvas.Canvas(temp_stamp_path, pagesize=letter)

#     # Load tick image
#     img = ImageReader(tick_image_path)
#     img_width, img_height = img.getSize()

#     # Reduce size further (10% of original)
#     scale = 0.1
#     img_width *= scale
#     img_height *= scale

#     # Draw tick image at bottom-right
#     # Adjust margin if needed
#     # Draw tick image at bottom-right, slightly lower
#     c.drawImage(img, width - img_width - 20, 5, width=img_width, height=img_height, mask='auto')

#     #c.drawImage(img, width - img_width - 20, 30, width=img_width, height=img_height, mask='auto')
#     c.save()

#     stamp_pdf = PdfReader(temp_stamp_path).pages[0]

#     # Overlay stamp on all pages
#     for page in reader.pages:
#         page.merge_page(stamp_pdf)
#         writer.add_page(page)

#     with open(output_pdf, "wb") as f:
#         writer.write(f)

#     os.remove(temp_stamp_path)
#     return output_pdf

# -------------------------------------
# ✅ Force download with green tick
# -------------------------------------
@frappe.whitelist(allow_guest=True)
def force_download(docname):
    doc = frappe.get_doc("Document Center", docname)
    if not doc.document:
        frappe.throw("No document attached!")

    if getattr(doc, "verification_status", None) != "Verified":
        frappe.throw("Please verify the digital signature before downloading.")

    file_doc = frappe.get_doc("File", {"file_url": doc.document})
    file_name = os.path.basename(file_doc.file_url)

    pdf_path = frappe.get_site_path("private", "files", file_name)
    if not os.path.exists(pdf_path):
        pdf_path = frappe.get_site_path("public", "files", file_name)
    if not os.path.exists(pdf_path):
        frappe.throw(f"File not found: {pdf_path}")

    # Green tick image path
    tick_image = frappe.get_site_path("private", "files", "green_verified_tick.png")
    if not os.path.exists(tick_image):
        frappe.throw("Green verified tick image not found!")

    stamped_output = frappe.get_site_path("private", "files", f"verified_{file_name}")

    # Overlay green tick
    overlay_verified_image(pdf_path, tick_image, stamped_output)

    # Attach stamped file as a new File record
    with open(stamped_output, "rb") as f:
        frappe.get_doc({
            "doctype": "File",
            "file_name": f"verified_{file_name}",
            "attached_to_doctype": "Document Center",
            "attached_to_name": docname,
            "content": f.read(),
            "is_private": 1
        }).insert(ignore_permissions=True)

    # Send stamped PDF for download
    with open(stamped_output, "rb") as f:
        frappe.local.response.filename = f"verified_{file_name}"
        frappe.local.response.filecontent = f.read()
        frappe.local.response.type = "download"

    frappe.msgprint("✅ Downloading verified & stamped PDF with green tick...")
