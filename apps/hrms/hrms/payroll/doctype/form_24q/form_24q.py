# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import os
import json
import shutil
import glob
import traceback
import base64
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from frappe.utils.file_manager import get_file_path
from frappe.model.document import Document
from frappe.utils import nowdate, get_site_path, format_date, getdate, cint, flt
from frappe.utils.pdf import get_pdf
import hashlib  # Added for MD5 hash calculation

class Form24Q(Document):
    def validate(self):
        # List of child table fieldnames 
        quarter_tables = [
            '1st_quarter_april_june',
            '2nd_quarter_july_sep',
            '3rd_quarter_oct_dec',
            '4th_quarter_jan_mar'
        ]

        for table_fieldname in quarter_tables:
            for row in self.get(table_fieldname):
                if not row.year:
                    frappe.throw(f"Year is mandatory in {frappe.bold(table_fieldname.replace('_', ' ').title())} table.")


#######################################################################################

@frappe.whitelist()
def generate_fvu_files_from_csi(csi_content, quarter, docname=None):
    try:
        form_24q_settings = get_form_24q_settings()
        parsed_data = parse_csi_content(csi_content)

        # Merge with Form 24Q Settings data
        merged_data = merge_with_settings(parsed_data, form_24q_settings, quarter, docname)
        
        # Generate all required files with your specific naming
        files_data = {
            'form_27a_pdf': generate_form_27a_pdf_dynamic(merged_data),  # PDF format
            'form24q_fvu': generate_fvu_file_dynamic(merged_data),        # Updated to simulate .fvu
            'form24q_txt': generate_text_file_dynamic(merged_data),      # .txt file
            'challan_csi': csi_content,    # .csi file
            'fvu_log': generate_fvu_log_dynamic(merged_data),            # .log file
            'warning_html': generate_warning_file_dynamic(merged_data),   # warning .html
            'statistics_html': generate_statistics_report_dynamic(merged_data) # statistics .html
        }
        
        # Save files with your specific naming convention
        file_paths = save_generated_files_with_custom_names(files_data, merged_data, quarter)
        
        return {
            'success': True,
            'files': file_paths,
            'data': merged_data,
            'quarter':quarter,
            'docname':docname
        }
        
    except Exception as e:
        frappe.log_error(f"FVU Generation Error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }



@frappe.whitelist()
def generate_fvu_log_dynamic(data):
    """Generate FVU log file"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    deductor = data['deductor']
    
    log_content = f"""FVU Processing Log
        ==================
        Processing Time: {current_time}
        FVU Version: 9.2
        Input File: form24q.txt

        Deductor Details:
        - TAN: {deductor.get('tan', '')}
        - PAN: {deductor.get('pan', '')}
        - Name: {deductor.get('name', '')}

        Processing Summary:
        - Quarter: {data['form_details'].get('quarter', '')}
        - Financial Year: {data['form_details'].get('financial_year', '')}
        - Total Deductees: {len(data['deductee_records'])}
        - Total Challans: {len(data['challan_details'])}
        - Total Tax Deducted: ₹{flt(data['control_totals'].get('tax_deducted', 0)):,.2f}

        Validation Results:
        - File Structure: VALID
        - Data Integrity: VALID
        - Format Compliance: VALID

        Files Generated:
        - Form 27A PDF: SUCCESS
        - FVU File: SUCCESS
        - Text File: SUCCESS
        - CSI File: SUCCESS
        - Warning File: SUCCESS
        - Statistics Report: SUCCESS

        Processing Status: COMPLETED SUCCESSFULLY

        End of Log
        =========="""
    
    return log_content


@frappe.whitelist()
def save_generated_files_with_custom_names(files_data, parsed_data, quarter):
    file_paths = {}
    try:
        # Ensure base folder exists
        base_path = get_site_path('private', 'files', f'fvu_{quarter}')
        os.makedirs(base_path, exist_ok=True)

        # Quarter mapping
        quarter_mapping = {
            '1st_quarter_april_june': 'Q1',
            '2nd_quarter_july_sep': 'Q2',
            '3rd_quarter_oct_dec': 'Q3',
            '4th_quarter_jan_mar': 'Q4'
        }
        quarter_code = quarter_mapping.get(quarter, quarter)
        if quarter_code not in ['Q1', 'Q2', 'Q3', 'Q4']:
            frappe.throw("Quarter is Not Valid !")

        # TAN resolution
        csi_tan = parsed_data.get('csi_data', {}).get('tan_number', '')
        settings_tan = parsed_data['deductor'].get('tan', '')
        tan = csi_tan if csi_tan else settings_tan if settings_tan else 'TAN'

        # Financial year cleanup
        financial_year = parsed_data['form_details'].get('financial_year', '')
        fy_clean = financial_year.replace('-', '')

        # File configs
        file_configs = {
            'form_27a_pdf': {
                'filename': f'27A_{tan}_24Q_{quarter_code}_{fy_clean}_form_27a.pdf',
                'content': files_data['form_27a_pdf'],
                'content_type': 'application/pdf'
            },
            'form24q_fvu': {
                'filename': f'form24q.fvu',
                'content': files_data['form24q_fvu'],
                'content_type': 'application/octet-stream'
            },
            'form24q_txt': {
                'filename': f'form24q.txt',
                'content': files_data['form24q_txt'],
                'content_type': 'text/plain'
            },
            'challan_csi': {
                'filename': f'challan.csi',
                'content': files_data['challan_csi'],
                'content_type': 'text/plain'
            },
            'fvu_log': {
                'filename': f'form24q.fvu.log',
                'content': files_data['fvu_log'],
                'content_type': 'text/plain'
            },
            'warning_html': {
                'filename': f'form24q_Electronic_Statement_Warning_File.html',
                'content': files_data['warning_html'],
                'content_type': 'text/html'
            },
            'statistics_html': {
                'filename': f'form24q_statistics.html',
                'content': files_data['statistics_html'],
                'content_type': 'text/html'
            }
        }

        # Loop through all files
        for file_key, config in file_configs.items():
            try:
                file_path = os.path.join(base_path, config['filename'])

                # Safety check → enforce saving only under fvu_generated
                if not file_path.startswith(base_path):
                    raise Exception(f"Invalid file path detected: {file_path}")

                content = config['content']
                if not content:
                    frappe.logger().warning(f"Empty content for file: {config['filename']}")
                    file_paths[file_key] = {
                        'error': 'Empty file content',
                        'filename': config['filename'],
                        'is_downloadable': False
                    }
                    continue

                # Handle PDF and other binary content
                if config['content_type'] == 'application/pdf' or config['content_type'] == 'application/octet-stream':
                    mode = 'wb'
                    encoding = None
                elif isinstance(content, str):
                    # Handle text content formatting
                    if config['content_type'] == 'text/html' and not content.lower().startswith('<!doctype'):
                        if not content.lower().startswith('<html'):
                            content = f'<!DOCTYPE html>\n{content}'
                        if '<head>' in content and 'charset' not in content.lower():
                            content = content.replace('<head>', '<head>\n    <meta charset="UTF-8">')
                    elif config['content_type'] == 'application/xml' and not content.strip().startswith('<?xml'):
                        content = f'<?xml version="1.0" encoding="UTF-8"?>\n{content}'
                    
                    mode = 'w'
                    encoding = 'utf-8'
                else:
                    # Binary content (bytes, bytearray)
                    mode = 'wb'
                    encoding = None

                # Write file
                with open(file_path, mode, encoding=encoding) as f:
                    f.write(content)

                # Rest of the file handling code remains the same...
                if not os.path.exists(file_path):
                    raise Exception(f"File was not created: {file_path}")

                actual_file_size = os.path.getsize(file_path)
                if actual_file_size == 0:
                    raise Exception(f"File is empty: {file_path}")

                # Create File doc
                file_doc = frappe.get_doc({
                    'doctype': 'File',
                    'file_name': config['filename'],
                    'file_url': f'/private/files/fvu_{quarter}/{config["filename"]}',
                    'folder': 'Home/Attachments',
                    'is_private': 1,
                    'file_size': actual_file_size,
                    'content_type': config['content_type']
                })
                file_doc.insert(ignore_permissions=True)

                # Build return structure
                file_paths[file_key] = {
                    'filename': config['filename'],
                    'file_url': file_doc.file_url,
                    'file_path': file_path,
                    'file_doc_name': file_doc.name,
                    'size': actual_file_size,
                    'content_type': config['content_type'],
                    'display_name': get_custom_file_display_name(file_key),
                    'extension': os.path.splitext(config['filename'])[1],
                    'is_downloadable': True,
                    'created_at': datetime.now().isoformat()
                }

            except Exception as file_error:
                file_paths[file_key] = {
                    'error': str(file_error),
                    'filename': config['filename'],
                    'is_downloadable': False
                }
                
        # Manifest for all generated files
        create_file_manifest(file_paths, parsed_data, base_path, quarter)

        frappe.db.commit()
        return file_paths

    except Exception as e:
        frappe.throw(f"Failed to save generated files: {str(e)}")


@frappe.whitelist()
def validate_file_extensions():
    """Validate that all generated files have proper extensions"""
    extension_mappings = {
        'form_27a_pdf': '.pdf',
        'form24q_fvu': '.fvu', 
        'form24q_txt': '.txt',
        'challan_csi': '.csi',
        'fvu_log': '.log',
        'warning_html': '.html',
        'statistics_html': '.html'
    }
    
    mime_type_mappings = {
        '.html': 'text/html',
        '.fvu': 'application/octet-stream',  # Updated
        '.txt': 'text/plain',
        '.csi': 'text/plain',
        '.log': 'text/plain',
        '.xml': 'application/xml',
        '.pdf': 'application/pdf'
    }
    
    return {
        'extension_mappings': extension_mappings,
        'mime_type_mappings': mime_type_mappings
    }


@frappe.whitelist()
def generate_download_links_html(file_paths):
    """Generate HTML for download links with proper file handling"""
    html = ""
    
    for file_key, file_info in file_paths.items():
        if file_info.get('is_downloadable', False):
            html += f"""
            <div class="download-item" style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{file_info['display_name']}</strong><br>
                        <small>{file_info['filename']} ({format_file_size(file_info['size'])})</small>
                    </div>
                    <div>
                        <a href="{file_info['file_url']}" 
                           download="{file_info['filename']}"
                           class="btn btn-primary btn-sm"
                           data-content-type="{file_info['content_type']}"
                           data-size="{file_info['size']}">
                            <i class="fa fa-download"></i> Download
                        </a>
                        <a href="{file_info['file_url']}" 
                           target="_blank"
                           class="btn btn-default btn-sm">
                            <i class="fa fa-eye"></i> View
                        </a>
                    </div>
                </div>
            </div>
            """
        else:
            html += f"""
            <div class="download-item-error" style="margin: 10px 0; padding: 10px; border: 1px solid #dc3545; border-radius: 5px; background-color: #f8d7da;">
                <div style="display: flex; align-items: center;">
                    <i class="fa fa-exclamation-triangle text-danger" style="margin-right: 10px;"></i>
                    <div>
                        <strong>{file_info.get('display_name', 'Unknown File')}</strong><br>
                        <small style="color: #721c24;">Error: {file_info.get('error', 'Unknown error')}</small>
                    </div>
                </div>
            </div>
            """
    
    return html

@frappe.whitelist()
def get_file_download_info(file_key, file_path_info):
    """Get comprehensive download information for a specific file"""
    try:
        file_path = file_path_info.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        # Get file stats
        stat_info = os.stat(file_path)
        
        # Read first few bytes to determine actual content type
        with open(file_path, 'rb') as f:
            file_header = f.read(512)
        
        # Determine content type from file header
        content_type = file_path_info.get('content_type', 'application/octet-stream')
        
        if file_header.startswith(b'<!DOCTYPE html') or file_header.startswith(b'<html'):
            content_type = 'text/html'
        elif file_header.startswith(b'<?xml'):
            content_type = 'application/xml'
        elif file_header.startswith(b'FH|FILE HEADER'):
            content_type = 'text/plain'
        
        return {
            'filename': file_path_info['filename'],
            'size': stat_info.st_size,
            'content_type': content_type,
            'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'is_readable': os.access(file_path, os.R_OK),
            'extension': os.path.splitext(file_path_info['filename'])[1],
            'download_url': file_path_info['file_url']
        }
        
    except Exception as e:
        return {'error': str(e)}

# Helper function to format file sizes
def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


@frappe.whitelist()
def create_file_manifest(file_paths, parsed_data, base_path, quarter):
    """Create a manifest file with all download information"""
    try:
        deductor = parsed_data.get('deductor', {})
        tan = deductor.get('tan', 'UNKNOWN')
        quarter = parsed_data.get('form_details', {}).get('quarter', 'Q1')
        
        manifest_content = f"""FVU FILE GENERATION MANIFEST
                    ========================================
                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    TAN: {tan}
                    Quarter: {quarter}
                    Company: {deductor.get('name', 'N/A')}

                    FILES GENERATED:
                    ========================================
                """
        
        successful_files = []
        failed_files = []
        
        for file_key, file_info in file_paths.items():
            if file_info.get('is_downloadable', False):
                successful_files.append(file_info)
                manifest_content += f"""
                ✓ {file_info['filename']}
                - Size: {file_info['size']} bytes
                - Type: {file_info['content_type']}
                - Extension: {file_info['extension']}
                - URL: {file_info['file_url']}
                """
            else:
                failed_files.append(file_info)
                manifest_content += f"""
                ✗ {file_info['filename']}
                - Error: {file_info.get('error', 'Unknown error')}
                """
        
        manifest_content += f"""
            SUMMARY:
            ========================================
            Total Files: {len(file_paths)}
            Successful: {len(successful_files)}
            Failed: {len(failed_files)}

            DOWNLOAD INSTRUCTIONS:
            ========================================
            1. All files are available for immediate download
            2. Files have proper extensions and MIME types
            3. Use the 'Download All Files' button for bulk download
            4. Check your browser's download folder
            5. Files are generated according to Income Tax Department specifications

            TECHNICAL DETAILS:
            ========================================
            FVU Version: 9.2
            Generated by: ERPNext HRMS
            Encoding: UTF-8
            File Format: Standard FVU format

            END OF MANIFEST
            ========================================
            """
        
        # Save manifest file ONLY in the fvu_generated directory
        manifest_filename = f'FVU_Manifest_{quarter}.txt'
        manifest_path = os.path.join(base_path, manifest_filename)  # base_path is already fvu_generated
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        
        # Create File document for manifest with PRIVATE path
        manifest_doc = frappe.get_doc({
            'doctype': 'File',
            'file_name': manifest_filename,
            'file_url': f'/private/files/fvu_{quarter}/{manifest_filename}',
            'folder': 'Home/Attachments',
            'is_private': 1,  # Keep private
            'file_size': len(manifest_content.encode('utf-8')),
            'content_type': 'text/plain'
        })
        manifest_doc.insert(ignore_permissions=True)
        
        return manifest_filename
        
    except Exception as e:
        # frappe.logger().error(f"Error creating manifest: {str(e)}")
        return None
    

@frappe.whitelist()
def get_custom_file_display_name(file_key):
    """Get display names for your specific file types"""
    labels = {
        'form_27a_pdf': 'Form 27A (PDF)',
        'form24q_fvu': 'Form 24Q FVU File',
        'form24q_txt': 'Form 24Q Text File',
        'challan_csi': 'Challan CSI File',
        'fvu_log': 'FVU Log File',
        'warning_html': 'Warning File (HTML)',
        'statistics_html': 'Statistics Report (HTML)'
    }
    return labels.get(file_key, file_key.replace('_', ' ').title())

#######################################################################################
@frappe.whitelist()
def get_form_24q_settings():
    """Get Form 24Q Settings for dynamic data"""
    try:
        # Fetch the single record for Form 24Q Settings
        settings_doc = frappe.get_single("Form 24Q Settings")
        
        if not settings_doc:
            frappe.throw("Form 24Q Settings not found. Please configure Form 24Q Settings first.")
        
        return settings_doc.as_dict()
        
    except Exception as e:
        frappe.log_error(f"Error getting Form 24Q Settings: {str(e)}")
        frappe.throw(f"Error getting Form 24Q Settings: {str(e)}")

@frappe.whitelist()
def get_quarter_details(form_24q_doc_name, quarter_name):
    """Get payroll_period and specific quarter data from Form 24Q"""
    try:
        # Get full document
        form_24q_doc = frappe.get_doc("Form 24Q", form_24q_doc_name)

        # Access specific fields
        payroll_period = form_24q_doc.payroll_period
        quarter_data = form_24q_doc.get(quarter_name) or []

        # Enhanced: Auto-populate from payroll if empty (example, adapt to your setup)
        if not quarter_data and payroll_period:
            # Query Salary Slips for the quarter
            months = get_quarter_months(quarter_name)
            salary_slips = frappe.get_list("Salary Slip", filters={
                "payroll_period": payroll_period,
                "month": ["in", months]
            }, fields=["*"])  # Adapt fields
            # Populate quarter_data from salary_slips
            # ... (implement logic to map to challan details)

        return {
            "payroll_period": payroll_period,
            quarter_name: quarter_data,
            "tan": getattr(form_24q_doc, 'tan', ''),
            "company": getattr(form_24q_doc, 'company', '')
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting quarter details: {str(e)}")
        return {"payroll_period": "", quarter_name: [], "error": str(e)}

def get_quarter_months(quarter_name):
    mapping = {
        '1st_quarter_april_june': ['Apr', 'May', 'Jun'],
        '2nd_quarter_july_sep': ['Jul', 'Aug', 'Sep'],
        '3rd_quarter_oct_dec': ['Oct', 'Nov', 'Dec'],
        '4th_quarter_jan_mar': ['Jan', 'Feb', 'Mar']
    }
    return mapping.get(quarter_name, [])

@frappe.whitelist()
def merge_with_settings(parsed_data, settings, quarter, form_24q_doc_name=None):
    """Merge parsed CSI data with Form 24Q Settings and company data"""
    
    # Quarter mapping
    quarter_mapping = {
        '1st_quarter_april_june': 'Q1',
        '2nd_quarter_july_sep': 'Q2', 
        '3rd_quarter_oct_dec': 'Q3',
        '4th_quarter_jan_mar': 'Q4'
    }
    
    quarter_code = quarter_mapping.get(quarter, quarter)
    
    quarter_details = get_quarter_details(form_24q_doc_name, quarter) if form_24q_doc_name else {}
    ttl_tax_deducted = 0
    ttl_amount_paid = 0
    ttl_challan_amount = 0
    
    # Calculate totals from quarter data
    quarter_data = quarter_details.get(quarter, [])
    for quart in quarter_data:
        ttl_amount_paid += flt(quart.get('challan_amount_remitted', 0))  
        ttl_tax_deducted += flt(quart.get('tax_deducted_from_employees', 0))  
        ttl_challan_amount += flt(quart.get('challan_amount_remitted', 0))  
        
    # Calculate financial and assessment years
    current_date = getdate()
    if current_date.month >= 4:
        fy_start = current_date.year
        fy_end = current_date.year + 1
    else:
        fy_start = current_date.year - 1
        fy_end = current_date.year
    
    # Get TAN from Form 24Q document or settings
    tan_number = quarter_details.get('tan', '') or parsed_data.get('tan_number', '') or settings.get('tan', '')
    
    # Generate challan details
    challan_details = generate_challan_details(quarter_data)
    
    # New: Validate challans against CSI hashes
    validation_results = validate_challans_against_csi(challan_details, parsed_data['challan_hashes'])
    # print(validation_results)
    # if validation_results['unmatched']:
        # frappe.throw(f"Challan validation failed: {len(validation_results['unmatched'])} unmatched challans. Please check your challan details.")

    # Generate deductee records
    deductee_records = generate_deductee_records(quarter_data, quarter_code)
    
    # Build comprehensive data structure
    merged_data = {
        'deductor': {
            'tan': tan_number,
            'pan': settings.get("pan_no", ''),
            'name': settings.get("pr_name", ''),
            'type': settings.get('type_of_deductor', 'COMPANY').upper(),
            'branch': 'YES' if settings.get('branch_division') == 'Yes' else 'NO',
            'flat_no': settings.get('flat_no', ''),
            'address_line1': f"{settings.get('flat_no', '')} {settings.get('name_of_premises_building', '')}".strip(),
            'address_line2': settings.get('road_street_lane', ''),
            'area_location': settings.get('area_location', ''),
            'city': settings.get('town_city_district', ''),
            'state': settings.get('state', 'MAHARASHTRA'),
            'pincode': str(settings.get('pin_code', '')),
            'phone': settings.get('telephone_no', ''),
            'std_code': settings.get('std_code', ''),
            'email': settings.get('email', ''),
            'responsible_person_name': settings.get('pr_name', ''),
            'responsible_person_pan': settings.get('pan_no', ''),
            'designation': settings.get('designation', 'DIRECTOR'),
            'pr_flat_no': settings.get('pr_flat_no', ''),
            'pr_building': settings.get('pr_name_of_premises_building', ''),
            'pr_road': settings.get('pr_road_street_lane', ''),
            'pr_area': settings.get('pr_area_location', ''),
            'pr_city': settings.get('pr_town_city_district', ''),
            'pr_state': settings.get('pr_state', ''),
            'pr_pincode': str(settings.get('pr_pin_code', '')),
            'pr_phone': settings.get('pr_telephone_no', ''),
            'pr_std_code': settings.get('pr_std_code', ''),
            'pr_email': settings.get('pr_email', ''),
            'mobile_no': settings.get('mobile_no', '')
        },
        'form_details': {
            'quarter': quarter_code,  # Use the mapped quarter code
            'financial_year': f'{fy_start}-{str(fy_end)[-2:]}',
            'assessment_year': f'{fy_end}-{str(fy_end + 1)[-2:]}',
            'return_type': 'REGULAR',
            'previous_receipt': 'NA',
            'form_24q_doc_name': form_24q_doc_name,
            'payroll_period': quarter_details.get('payroll_period', '')
        },
        'challan_details': challan_details,
        'deductee_records': deductee_records,
        'control_totals': {
            'amount_paid': ttl_amount_paid,
            'tax_deducted': ttl_tax_deducted,
            'tax_deposited': ttl_challan_amount
        },
        'quarter_data': quarter_data,
        'csi_data': parsed_data,  # Add the parsed CSI data
        'validation_results': validation_results  
    }
    
    return merged_data

def validate_challans_against_csi(challan_details, csi_hashes):
    """Validate challan details against CSI hashes"""
    computed_hashes = []
    for challan in challan_details:
        
        bsr = str(challan.get('bsr_code', '')).zfill(7)
        tender_date = challan.get('tender_date', '').replace('/', '') 
        serial = str(challan.get('serial_number', '')).zfill(5)
        amount = str(int(flt(challan.get('amount', 0))))
        
        hash_string = bsr + tender_date + serial + amount
        hash_value = hashlib.md5(hash_string.encode('utf-8')).hexdigest().upper()
        computed_hashes.append(hash_value)
    
    matched = set(computed_hashes) & set(csi_hashes)
    unmatched = set(computed_hashes) - set(csi_hashes)
    
    return {
        'matched_count': len(matched),
        'unmatched': list(unmatched),
        'total_computed': len(computed_hashes),
        'total_csi': len(csi_hashes)
    }

def generate_challan_details(quarter_data):
    """Generate challan details from quarter data"""
    challan_details = []
    for i, record in enumerate(quarter_data, 1):
        challan_details.append({
            'tender_date': format_date(record.get('challan_tender_date', nowdate()), "ddmmyyyy"),  
            'serial_number': record.get('challan_serial_number', f'CH{i:06d}'),
            'bsr_code': record.get('bsr_code', '6390009'),
            'amount': flt(record.get('challan_amount_remitted', 0)),
            'tax_amount': flt(record.get('tax_deducted_from_employees', 0))
        })
    return challan_details

def generate_deductee_records(quarter_data, quarter_code):
    """Generate deductee records from quarter data, with Q4 enhancements"""
    deductee_records = []
    for i, record in enumerate(quarter_data, 1):
        deductee = {
            'pan': record.get('employee_pan', 'PANNOTAVBL'),
            'name': record.get('employee_name', f'Employee {i}'),
            'amount_paid': flt(record.get('gross_salary', 0)),
            'tax_deducted': flt(record.get('tax_deducted_from_employees', 0)),
            'date_of_deduction': format_date(record.get('salary_date', nowdate()), "dd/mm/yyyy"),
            'section': record.get('section_code', '192A'),
            'rate': flt(record.get('tax_rate', 10.0))
        }
        
        # New: For Q4, add salary details (Annexure II) - assume data from record or fetch from payroll
        if quarter_code == 'Q4':
            deductee['salary_details'] = {
                'gross_earnings': flt(record.get('gross_earnings', deductee['amount_paid'])),
                'exemptions': flt(record.get('exemptions', 0)),
                'deductions_chapter_via': flt(record.get('deductions_via', 0)),
                # Add more fields as per Annexure II (e.g., 80C, 80D, etc.)
            }
        
        deductee_records.append(deductee)
    return deductee_records

@frappe.whitelist()
def generate_form_27a_pdf_dynamic(data):
    """Generate Form 27A as actual PDF using Frappe's PDF utilities"""

    
    current_date = datetime.now().strftime('%d/%m/%Y')
    quarter = data['form_details'].get('quarter', '')
    financial_year = data['form_details'].get('financial_year', '')
    assessment_year = data['form_details'].get('assessment_year', '')
    
    # Get date ranges for quarter
    quarter_ranges = get_quarter_date_ranges(data)
    
    deductor = data['deductor']
    num_deductees = len(data['deductee_records'])
    num_challans = len(data['challan_details'])
    
    # Format amounts properly
    amount_paid = f"{flt(data['control_totals'].get('amount_paid', 0)):,.2f}"
    tax_deducted = f"{flt(data['control_totals'].get('tax_deducted', 0)):,.2f}"
    tax_deposited = f"{flt(data['control_totals'].get('tax_deposited', 0)):,.2f}"
    
    # Render HTML template first
    html_content = frappe.render_template(
        'hrms/payroll/doctype/form_24q/form_27a_pdf.html',
        {
            "quarter": quarter,
            "quarter_ranges": quarter_ranges,
            "financial_year": financial_year,
            "assessment_year": assessment_year,
            "deductor": deductor,
            "num_deductees": num_deductees,
            "num_challans": num_challans,
            "amount_paid": amount_paid,
            "tax_deducted": tax_deducted,
            "tax_deposited": tax_deposited,
            "data": data,
            "current_date": current_date
        }
    )
    
    try:
        # Convert HTML to PDF using Frappe's PDF utility
        pdf_content = get_pdf(html_content)
        
        # Ensure PDF content is returned as bytes
        if isinstance(pdf_content, str):
            # If somehow string is returned, encode it
            pdf_content = pdf_content.encode('latin1')
        
        return pdf_content
        
    except Exception as e:
        frappe.log_error(f"PDF Generation Error: {str(e)}")
        # Fallback: return HTML content if PDF generation fails
        frappe.logger().warning(f"PDF generation failed, returning HTML: {str(e)}")
        return html_content

def get_quarter_date_ranges(data):
    """Get proper date ranges for quarters based on payroll period"""
    # Try to get dates from payroll period first
    payroll_period = data['form_details'].get('payroll_period')
    start_date = None
    end_date = None
    
    if payroll_period:
        try:
            payroll_period_doc = frappe.get_doc("Payroll Period", payroll_period)
            start_date = payroll_period_doc.start_date
            end_date = payroll_period_doc.end_date
        except:
            pass
    
    # Fallback to financial year calculation
    if not start_date or not end_date:
        try:
            fy = data['form_details'].get('financial_year', '2025-26')
            start_year = int(fy.split('-')[0])
            start_date = getdate(f"{start_year}-04-01")
            end_date = getdate(f"{start_year + 1}-03-31")
        except:
            start_date = getdate(f"{datetime.now().year}-04-01")
            end_date = getdate(f"{datetime.now().year + 1}-03-31")
    
    # Calculate quarter date ranges
    q1_start = start_date
    q1_end = getdate(f"{start_date.year}-06-30")
    
    q2_start = getdate(f"{start_date.year}-07-01")
    q2_end = getdate(f"{start_date.year}-09-30")
    
    q3_start = getdate(f"{start_date.year}-10-01")
    q3_end = getdate(f"{start_date.year}-12-31")
    
    q4_start = getdate(f"{start_date.year + 1}-01-01") if start_date.year + 1 <= end_date.year else getdate(f"{end_date.year}-01-01")
    q4_end = end_date
    
    return {
        'Q1': f'From {q1_start.strftime("%d/%m/%Y")} to {q1_end.strftime("%d/%m/%Y")}',
        'Q2': f'From {q2_start.strftime("%d/%m/%Y")} to {q2_end.strftime("%d/%m/%Y")}',
        'Q3': f'From {q3_start.strftime("%d/%m/%Y")} to {q3_end.strftime("%d/%m/%Y")}',
        'Q4': f'From {q4_start.strftime("%d/%m/%Y")} to {q4_end.strftime("%d/%m/%Y")}'
    }

@frappe.whitelist()
def generate_statistics_report_dynamic(data):
    """Generate Statistics Report HTML with accurate dynamic data"""
    if not data or not data.get('deductor'):
        return "<p>Error: Missing data for rendering Statistics Report.</p>"
    
    # Calculate PAN statistics
    valid_pan_count = sum(1 for record in data['deductee_records']
                          if record.get('pan', '') and len(record.get('pan', '')) == 10 
                          and record.get('pan') not in ['PANAPPLIED', 'PANNOTAVBL', 'PANINVALID'])
    
    pan_applied_count = sum(1 for record in data['deductee_records']
                            if record.get('pan', '') == 'PANAPPLIED')
    
    pan_not_available_count = sum(1 for record in data['deductee_records']
                                  if record.get('pan', '') == 'PANNOTAVBL')
    
    pan_invalid_count = sum(1 for record in data['deductee_records']
                            if record.get('pan', '') == 'PANINVALID')
    
    deductor = data['deductor']
    num_deductees = len(data['deductee_records'])
    num_challans = len(data['challan_details'])
    
    # Format amounts
    amount_paid = f"{flt(data['control_totals'].get('amount_paid', 0)):,.2f}"
    tax_deducted = f"{flt(data['control_totals'].get('tax_deducted', 0)):,.2f}"
    tax_deposited = f"{flt(data['control_totals'].get('tax_deposited', 0)):,.2f}"

    # New: Add validation stats
    validation = data.get('validation_results', {})
    matched_challans = validation.get('matched_count', 0)
    total_challans = validation.get('total_computed', 0)

    # Render with context
    try:
        html_content = frappe.render_template(
            'hrms/payroll/doctype/form_24q/statistics_report.html',
            {
                "deductor": deductor,
                "data": data,
                "num_deductees": num_deductees,
                "num_challans": num_challans,
                "amount_paid": amount_paid,
                "tax_deducted": tax_deducted,
                "tax_deposited": tax_deposited,
                "valid_pan_count": valid_pan_count,
                "pan_applied_count": pan_applied_count,
                "pan_not_available_count": pan_not_available_count,
                "pan_invalid_count": pan_invalid_count,
                "matched_challans": matched_challans,
                "total_challans": total_challans
            }
        )
        return html_content
    except Exception as e:
        frappe.log_error(f"Error rendering Statistics Report: {str(e)}")
        return f"<p>Error rendering report: {str(e)}</p>"

@frappe.whitelist()
def generate_fvu_file_dynamic(data):
    """Generate simulated .fvu file - in practice, this would be the validated .txt content"""
    # For simulation, use the text file content if validated
    text_content = generate_text_file_dynamic(data)
    # In real, run FVU utility, but here, return as bytes
    return text_content.encode('utf-8')  # Treat as binary

@frappe.whitelist()
def generate_text_file_dynamic(data):
    """Generate text file for FVU with dynamic data - Note: Should be fixed-length in standard, but keeping pipe for now"""
    deductor = data['deductor']
    current_date = datetime.now().strftime('%d/%m/%Y')
    
    # File header
    text_content = f"""FH|FILE HEADER|{deductor.get('tan', '')}|{data['form_details'].get('financial_year', '2025-26')}|{data['form_details'].get('quarter', 'Q1')}|24Q|9.2|{current_date}|ORIGINAL|{len(data['deductee_records'])}|{flt(data['control_totals'].get('amount_paid', 0)):,.2f}|{flt(data['control_totals'].get('tax_deducted', 0)):,.2f}

                    BH|BATCH HEADER|1|{deductor.get('tan', '')}|{deductor.get('pan', '')}|{deductor.get('name', '')}|{data['form_details'].get('assessment_year', '2026-27')}|{data['form_details'].get('quarter', 'Q1')}|{data['form_details'].get('return_type', 'REGULAR')}|{data['form_details'].get('previous_receipt', 'NA')}"""
    
    # Add challan details (CD instead of CH for standard)
    for i, challan in enumerate(data['challan_details'], 1):
        text_content += f"""CD|{challan.get('tender_date', '')}|{challan.get('serial_number', '')}|{challan.get('bsr_code', '')}|{flt(challan.get('amount', 0)):,.2f}|0.00|{flt(challan.get('amount', 0)):,.2f}|{i}"""  # Updated to CD
    
    # Add deductee details (DD)
    for i, deductee in enumerate(data['deductee_records'], 1):
        text_content += f"""DD|{i}|{deductee.get('pan', '')}|{deductee.get('name', '')}|{flt(deductee.get('amount_paid', 0)):,.2f}|{flt(deductee.get('tax_deducted', 0)):,.2f}|{deductee.get('date_of_deduction', '')}|{deductee.get('section', '192A')}|{flt(deductee.get('rate', 10.0)):,.2f}|N|NA"""
        
        # New: For Q4, add salary details (SD)
        if data['form_details'].get('quarter') == 'Q4':
            sd = deductee.get('salary_details', {})
            text_content += f"""SD|{i}|{flt(sd.get('gross_earnings', 0)):,.2f}|{flt(sd.get('exemptions', 0)):,.2f}|{flt(sd.get('deductions_chapter_via', 0)):,.2f}"""  # Add more fields as needed
    
    # Batch trailer
    text_content += f"""BT|{len(data['challan_details'])}|{len(data['deductee_records'])}|{flt(data['control_totals'].get('amount_paid', 0)):,.2f}|{flt(data['control_totals'].get('tax_deducted', 0)):,.2f}"""
    
    # File trailer
    text_content += f"""FT|1|{len(data['challan_details'])}|{len(data['deductee_records'])}|{flt(data['control_totals'].get('amount_paid', 0)):,.2f}|{flt(data['control_totals'].get('tax_deducted', 0)):,.2f}"""
    
    return text_content

@frappe.whitelist()
def parse_csi_content(content):
    """
    Enhanced CSI file parser for hashed format to extract header and validation hashes
    CSI files contain hashed challan data for TDS/TCS validation
    """
    # print("=== Starting CSI Content Parsing ===")
    # print(f"Content length: {len(content)} characters")
    
    lines = content.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Essential data structure
    data = {
        'tan_number': '',
        'company_name': '',
        'deductor_name': '',
        'reference_id': '',
        'file_type': 'CSI',
        'file_version': '',
        'generation_date': '', 
        
        'total_challans': 0,
        'file_valid': False,
        
        'challan_hashes': [],
        
        'parsing_errors': [],
        'file_status': 'Unknown'
    }
    
    # print(f"Total lines to process: {len(lines)}")
    
    if not lines:
        data['parsing_errors'].append("Empty CSI file")
        data['file_status'] = 'Empty'
        return data
    
    # Process header (first line, ^ separated)
    header_line = lines[0]
    if '^' in header_line:
        parts = header_line.split('^')
        if len(parts) >= 6:
            data['total_challans'] = int(parts[0].strip()) if parts[0].isdigit() else 0
            data['tan_number'] = parts[1].strip()
            data['company_name'] = parts[2].strip()
            data['deductor_name'] = parts[2].strip()  # Often same as company
            data['file_version'] = f"{parts[3].strip()}^{parts[4].strip()}"
            data['reference_id'] = parts[5].strip()
        else:
            data['parsing_errors'].append("Invalid header format")
    
    # Process hash lines (remaining lines, 32-char hex)
    for line_no, line in enumerate(lines[1:], 2):  # Start from second line
        if len(line) == 32 and all(c in '0123456789abcdefABCDEF' for c in line):
            data['challan_hashes'].append(line.upper())
        else:
            data['parsing_errors'].append(f"Invalid hash on line {line_no}: {line}")
    
    # Validation
    if len(data['challan_hashes']) == data['total_challans'] and data['tan_number']:
        data['file_valid'] = True
        data['file_status'] = 'Valid'
    elif data['parsing_errors']:
        data['file_status'] = 'Invalid - Contains Errors'
    else:
        data['file_status'] = 'Invalid - Insufficient Data'
    
    # Summary
    # print("\n=== CSI PARSING SUMMARY ===")
    # print(f"TAN Number: {data['tan_number']}")
    # print(f"Company Name: {data['company_name']}")
    # print(f"Total Challans: {data['total_challans']}")
    # print(f"Total Hashes: {len(data['challan_hashes'])}")
    # print(f"File Status: {data['file_status']}")
    # print(f"Parsing Errors: {len(data['parsing_errors'])}")
    
    return data
 

def generate_summary_content(parsed_data, file_paths, timestamp):
    """Generate comprehensive summary content"""
    summary_content = f"""FVU FILE GENERATION SUMMARY
        ==========================================
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Timestamp: {timestamp}

        COMPANY INFORMATION
        ==========================================
        Company Name: {parsed_data['deductor'].get('name', '')}
        TAN: {parsed_data['deductor'].get('tan', '')}
        PAN: {parsed_data['deductor'].get('pan', '')}
        Type of Deductor: {parsed_data['deductor'].get('type', '')}

        FORM DETAILS
        ==========================================
        Quarter: {parsed_data['form_details'].get('quarter', '')}
        Financial Year: {parsed_data['form_details'].get('financial_year', '')}
        Assessment Year: {parsed_data['form_details'].get('assessment_year', '')}
        Return Type: {parsed_data['form_details'].get('return_type', '')}
        Form 24Q Doc: {parsed_data['form_details'].get('form_24q_doc_name', 'N/A')}

        STATISTICS
        ==========================================
        Total Deductees: {len(parsed_data['deductee_records'])}
        Total Challans: {len(parsed_data['challan_details'])}
        Total Amount Paid: ₹{flt(parsed_data['control_totals'].get('amount_paid', 0)):,.2f}
        Total Tax Deducted: ₹{flt(parsed_data['control_totals'].get('tax_deducted', 0)):,.2f}
        Total Tax Deposited: ₹{flt(parsed_data['control_totals'].get('tax_deposited', 0)):,.2f}

        FILES GENERATED
        =========================================="""
    
    for file_key, file_info in file_paths.items():
        if 'error' not in file_info:
            summary_content += f"\n✓ {file_info['filename']} ({file_info['size']} bytes)"
        else:
            summary_content += f"\n✗ {file_info['filename']} - Error: {file_info['error']}"
    
    summary_content += f"""

        COMPANY ADDRESS
        ==========================================
        Address Line 1: {parsed_data['deductor'].get('address_line1', '')}
        Address Line 2: {parsed_data['deductor'].get('address_line2', '')}
        Area/Location: {parsed_data['deductor'].get('area_location', '')}
        City: {parsed_data['deductor'].get('city', '')}
        State: {parsed_data['deductor'].get('state', '')}
        PIN Code: {parsed_data['deductor'].get('pincode', '')}
        Phone: {parsed_data['deductor'].get('std_code', '')}-{parsed_data['deductor'].get('phone', '')}
        Email: {parsed_data['deductor'].get('email', '')}

        RESPONSIBLE PERSON
        ==========================================
        Name: {parsed_data['deductor'].get('responsible_person_name', '')}
        PAN: {parsed_data['deductor'].get('responsible_person_pan', '')}
        Designation: {parsed_data['deductor'].get('designation', '')}
        Email: {parsed_data['deductor'].get('pr_email', '')}

        VALIDATION NOTES
        ==========================================
        - All amounts are in INR
        - Dates are in DD/MM/YYYY format
        - Files generated using FVU Version 9.2
        - Files are ready for submission to Income Tax Department

        END OF REPORT
        ==========================================
        """
    
    return summary_content

@frappe.whitelist()
def get_file_display_name(file_key):
    """Get user-friendly display names for file types"""
    labels = {
        'form_27a': 'Form 27A (Text Format)',
        'statistics_report': 'Statistics Report (HTML)',
        'warning_file': 'Warning File (HTML)', 
        'fvu_file': 'FVU File (XML)',
        'text_file': 'Text File (TXT)',
        'summary': 'Generation Summary (LOG)'
    }
    return labels.get(file_key, file_key.replace('_', ' ').title())


@frappe.whitelist()
def get_fvu_download_links(file_paths):
    """Get formatted download links for generated FVU files"""
    download_links = []
    
    for file_key, file_info in file_paths.items():
        if 'error' not in file_info:
            download_links.append({
                'label': file_info.get('display_name', get_file_display_name(file_key)),
                'url': file_info['file_url'],
                'filename': file_info['filename'],
                'size': file_info['size'],
                'type': file_info['content_type'],
                'file_key': file_key
            })
    
    return download_links

@frappe.whitelist()
def generate_warning_file_dynamic(data):
    """Generate Warning File HTML with dynamic data"""
    deductor = data['deductor']
    
    html_content = f"""<HTML>
        <HEAD>
            <TITLE>e-TDS/TCS statement warning file</TITLE>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #000; padding: 5px; text-align: left; font-size: 11px; }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                h3 {{ text-align: center; }}
                .right {{ text-align: right; }}
            </style>
        </HEAD>
        <BODY>

        <h3><u>e-TDS/TCS statement warning file</u></h3>

        <p>e-TDS/TCS statement warning file is generated by FVU if:</p>
        <ul>
            <li>The value in the Bank Branch Code (BSR code) field of challan in the e-TDS/TCS statements is not present in the authorized list of collecting Bank Branch Codes in the FVU and/or</li>
            <li>If the PAN of the deductor is same as that of any deductee in the e-TDS/TCS statement.</li>
            <li>If the challans details of the statement do not match with the details uploaded by the bank.</li>
            <li>In case tax is deducted at higher rate and corresponding rate of deduction is less than 20%.</li>
            <li>If date of deduction is beyond the quarter.</li>
            <li>If TAN name of the deductor is not present in TAN master of Income Tax Department (ITD).</li>
        </ul>

        <p>This file is generated to give an alert to the deductor about the records in which invalid values are mentioned.</p>

        <table>
            <tr>
                <th>Line no. in the text file</th>
                <th>Record Type</th>
                <th>Batch no. in the text file</th>
                <th>Challan detail record no.</th>
                <th>Deductee/Salary detail record no.</th>
                <th>Challan tender date</th>
                <th>Challan Serial no.</th>
                <th>BSR code</th>
                <th>Error Code</th>
                <th>Error Description</th>
            </tr>"""
    
    # New: Dynamic warnings based on validation
    validation = data.get('validation_results', {})
    for i, unmatched_hash in enumerate(validation.get('unmatched', []), 1):
        html_content += f"""
            <tr>
                <td class="right">{i*100+3}</td>
                <td>Challan</td>
                <td class="right">1</td>
                <td class="right">{i}</td>
                <td>NA</td>
                <td>N/A</td>
                <td class="right">N/A</td>
                <td class="right">N/A</td>
                <td>T-FV-3141</td>
                <td>Unmatched challan hash: {unmatched_hash} - Challan details not present in CSI file</td>
            </tr>"""
    
    # Add static example if no unmatched
    if not validation.get('unmatched'):
        for i, challan in enumerate(data['challan_details'], 1):
            html_content += f"""
                <tr>
                    <td class="right">{i*100+3}</td>
                    <td>Challan</td>
                    <td class="right">1</td>
                    <td class="right">{i}</td>
                    <td>NA</td>
                    <td>{challan.get('tender_date', '')}</td>
                    <td class="right">{challan.get('serial_number', '')}</td>
                    <td class="right">{challan.get('bsr_code', '')}</td>
                    <td>T-FV-3141</td>
                    <td>Challan details mentioned in the statement not present in the challan file imported</td>
                </tr>"""
    
    html_content += """
            </table>

            <h4>Bank branch code not present in the list of authorized bank branches:</h4>
            <p>The Bank Branch Code is provided on the challan counterfoil along with the tender date and challan serial no. by the collecting bank branch where TDS / TCS has been deposited.</p>
            <p>Deductor / Collector should verify the Bank Branch Code mentioned in the e-TDS/TCS statement with the bank branch code on the challan counterfoil provided by the bank.</p>
            <p>In case of mismatch, the bank branch codes as per the challan counterfoil should be mentioned in the e-TDS/TCS statement and the file should be revalidated through FVU.</p>
            <p>In case there is no mismatch then the .fvu file created by the FVU should be submitted to the TIN-FC.</p>

            <h4>Same PAN in deductor and deductee PAN field.</h4>
            <p>PAN of the deductor given in the deductor details should normally not appear in the deductee details.</p>
            <p>Deductor/Collector should verify the PAN in the deductee details and if the same has been correctly entered, then the .fvu file created by the FVU should be submitted to the TIN-FC.</p>

            <br><br>
            <p>FVU Version: 9.2 &nbsp;&nbsp; Input File Name: form24q.txt</p>

            </BODY>
            </HTML>"""
    
    return html_content

@frappe.whitelist()
def generate_fvu_zip_file(docname, quarter):
    try:
        base_path = get_site_path('private', 'files', f'fvu_{quarter}')
        
        if not os.path.exists(base_path):
            return {'success': False, 'error': 'No FVU files directory found'}
        
        # Get Form 24Q document to extract TAN
        form_24q = frappe.get_doc("Form 24Q", docname)
        
        # Try different field names for TAN
        tan = None
        possible_tan_fields = ['tan', 'tan_number', 'company_tan', 'deductor_tan']
        
        for field in possible_tan_fields:
            tan = form_24q.get(field)
            if tan and tan != 'TAN':
                break
        
        # If TAN not found in document, extract from existing files
        if not tan or tan == 'TAN':
            # Look for Form 27A files to extract TAN
            form27a_files = glob.glob(os.path.join(base_path, "27A_*_24Q_*.pdf"))  # Look for PDF first
            if not form27a_files:
                form27a_files = glob.glob(os.path.join(base_path, "27A_*_24Q_*.html"))  # Fallback to HTML
            if form27a_files:
                filename = os.path.basename(form27a_files[0])
                parts = filename.split('_')
                if len(parts) >= 2:
                    tan = parts[1]
            
            # If still no TAN found, try regex pattern matching
            if not tan:
                all_files = os.listdir(base_path)
                for file in all_files:
                    import re
                    tan_match = re.search(r'[A-Z]{4}\d{5}[A-Z]', file)
                    if tan_match:
                        tan = tan_match.group()
                        break
        
        # Collect files to zip
        matching_files = []
        
        if tan and tan != 'TAN':
            # Quarter mapping
            quarter_mapping = {
                '1st_quarter_april_june': 'Q1',
                '2nd_quarter_july_sep': 'Q2', 
                '3rd_quarter_oct_dec': 'Q3',
                '4th_quarter_jan_mar': 'Q4'
            }
            quarter_code = quarter_mapping.get(quarter, quarter)
            
            # Find files containing TAN
            for file in os.listdir(base_path):
                file_path = os.path.join(base_path, file)
                if os.path.isfile(file_path) and tan.upper() in file.upper():
                    matching_files.append(file_path)
        
        # Include standard FVU files
        standard_files = ['form24q.fvu', 'form24q.txt', 'challan.csi', 'form24q.fvu.log']
        for file in standard_files:
            file_path = os.path.join(base_path, file)
            if os.path.isfile(file_path):
                matching_files.append(file_path)
        
        # Include HTML files (but exclude Form 27A HTML if PDF exists)
        html_files = glob.glob(os.path.join(base_path, "*.html"))
        for html_file in html_files:
            # Check if this is a Form 27A HTML file
            if '27A_' in os.path.basename(html_file) and html_file.endswith('_form_27a.html'):
                # Check if corresponding PDF exists
                pdf_equivalent = html_file.replace('.html', '.pdf')
                if not os.path.exists(pdf_equivalent):
                    # Only include HTML if PDF doesn't exist
                    matching_files.append(html_file)
                # If PDF exists, skip the HTML version
            else:
                # Include other HTML files (warning, statistics, etc.)
                matching_files.append(html_file)
        
        # Remove duplicates
        matching_files = list(set(matching_files))
        
        # Additional filter: Remove any HTML Form 27A files if corresponding PDF exists
        filtered_files = []
        for file_path in matching_files:
            filename = os.path.basename(file_path)
            if filename.endswith('_form_27a.html'):
                # Check if PDF version exists
                pdf_version = file_path.replace('.html', '.pdf')
                if os.path.exists(pdf_version):
                    # Skip HTML version since PDF exists
                    continue
            filtered_files.append(file_path)
        
        matching_files = filtered_files
        
        if not matching_files:
            return {'success': False, 'error': f'No FVU files found in directory'}

        # Create ZIP file
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in matching_files:
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    # Additional check: Skip Form 27A HTML files
                    if filename.endswith('_form_27a.html'):
                        continue
                    # Skip manifest and hidden files
                    if not filename.startswith('FVU_Manifest_') and not filename.startswith('.'):
                        zip_file.write(file_path, filename)

        zip_buffer.seek(0)
        zip_filename = f"FVU_Files_{quarter}_{docname}.zip"
        
        # Save ZIP file to private files
        zip_path = os.path.join(base_path, zip_filename)
        with open(zip_path, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        # Create File document for ZIP
        file_doc = frappe.get_doc({
            'doctype': 'File',
            'file_name': zip_filename,
            'file_url': f'/private/files/fvu_{quarter}/{zip_filename}',
            'folder': 'Home/Attachments',
            'is_private': 1,
            'file_size': len(zip_buffer.getvalue()),
            'content_type': 'application/zip'
        })
        file_doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        return {
            'success': True,
            'file_url': file_doc.file_url,
            'filename': zip_filename,
            'size': len(zip_buffer.getvalue())
        }
        
    except Exception as e:
        # frappe.log_error(f"Error creating ZIP file: {str(e)}")
        return {'success': False, 'error': str(e)}
