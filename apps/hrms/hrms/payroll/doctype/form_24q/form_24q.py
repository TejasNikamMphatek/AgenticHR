# Copyright (c) 2025, mPHATEK Systems Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, get_site_path
import os
import json
from datetime import datetime, timedelta
import base64

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

@frappe.whitelist()
def generate_fvu_files_from_csi(csi_content, quarter):
    try:
        # Parse CSI content
        parsed_data = parse_csi_content(csi_content)
        
        # Generate all required files
        files_data = {
            'form_27a': generate_form_27a(parsed_data),
            'statistics_report': generate_statistics_report(parsed_data),
            'warning_file': generate_warning_file(parsed_data),
            'fvu_file': generate_fvu_xml(parsed_data),
            'text_file': generate_text_file(parsed_data)
        }
        
        # Save files to site files
        file_paths = save_generated_files(files_data, parsed_data)
        
        return {
            'success': True,
            'files': file_paths,
            'data': parsed_data
        }
        
    except Exception as e:
        frappe.log_error(f"FVU Generation Error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def parse_csi_content(content):
    """Parse CSI file content and extract data"""
    lines = content.split('\n')
    data = {
        'deductor': {},
        'challan_details': [],
        'deductee_records': [],
        'control_totals': {},
        'form_details': {}
    }
    
    current_record = {}
    record_type = ''
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('|')
        if len(parts) < 2:
            continue
            
        field = parts[0]
        value = parts[1] if len(parts) > 1 else ''
        
        # Parse different record types
        if field.startswith('DEDUCTOR_'):
            field_name = field.replace('DEDUCTOR_', '').lower()
            data['deductor'][field_name] = value
        elif field.startswith('FORM_'):
            field_name = field.replace('FORM_', '').lower()
            data['form_details'][field_name] = value
        elif field.startswith('CHALLAN_'):
            if field == 'CHALLAN_START':
                current_record = {'type': 'challan'}
            elif field == 'CHALLAN_END':
                if current_record:
                    data['challan_details'].append(current_record.copy())
                current_record = {}
            else:
                field_name = field.replace('CHALLAN_', '').lower()
                current_record[field_name] = value
        elif field.startswith('DEDUCTEE_'):
            if field == 'DEDUCTEE_START':
                current_record = {'type': 'deductee'}
            elif field == 'DEDUCTEE_END':
                if current_record:
                    data['deductee_records'].append(current_record.copy())
                current_record = {}
            else:
                field_name = field.replace('DEDUCTEE_', '').lower()
                current_record[field_name] = value
        elif field.startswith('TOTAL_'):
            field_name = field.replace('TOTAL_', '').lower()
            data['control_totals'][field_name] = value
    
    return data

@frappe.whitelist()
def generate_form_27a(data):
    """Generate Form 27A content"""
    current_date = datetime.now().strftime('%d/%m/%Y')
    quarter = data['form_details'].get('quarter', 'Q1')
    financial_year = data['form_details'].get('financial_year', '2025-26')
    assessment_year = data['form_details'].get('assessment_year', '2026-27')
    
    # Generate quarter date ranges
    quarter_ranges = {
        'Q1': 'From 01/04/25 to 30/06/25',
        'Q2': 'From 01/07/25 to 30/09/25',
        'Q3': 'From 01/10/25 to 31/12/25',
        'Q4': 'From 01/01/26 to 31/03/26'
    }
    
    form_27a_content = f"""File Hash 
        00000000000731491859
        25072307132831491859
        Form No. 27A
        Form for furnishing information with the statement of deduction / collection of tax at source ( tick whichever is applicable ) filed on computer media for the period {quarter}
        ({quarter_ranges.get(quarter, quarter_ranges['Q1'])} (dd/mm/yy)#)

        1 (a) Tax Deduction Account No. 
        {data['deductor'].get('tan', '')} 
        (d) Financial Year 
        {financial_year}
        (b) Permanent Account No. 
        {data['deductor'].get('pan', '')} 
        (e) Assessment year 
        {assessment_year}
        (c) Form No. 
        24Q 
        (f) Previous receipt number 
        {data['form_details'].get('previous_receipt', 'NA')}
        (In case return/statement has
        been filed earlier)

        2 Particulars of the deductor / collector 3 Name of the person responsible for deduction / collection of tax
        (a) Name {data['deductor'].get('name', '')}
        (b) Type of deductor* {data['deductor'].get('type', 'COMPANY')}
        (c) Branch / division (if any) {data['deductor'].get('branch', 'NO')}
        (d) Address
        {data['deductor'].get('address_line1', '')}
        {data['deductor'].get('address_line2', '')}
        {data['deductor'].get('city', '')}
        {data['deductor'].get('state', '')}
        {data['deductor'].get('pincode', '')}
        Telephone No. {data['deductor'].get('phone', '')}
        E-mail {data['deductor'].get('email', '')}

        (a)Name {data['deductor'].get('responsible_person_name', '')}
        (b)PAN {data['deductor'].get('responsible_person_pan', '')}
        (c)Address
        {data['deductor'].get('address_line1', '')}
        {data['deductor'].get('address_line2', '')}
        {data['deductor'].get('city', '')}
        {data['deductor'].get('state', '')}
        {data['deductor'].get('pincode', '')}
        Telephone No. {data['deductor'].get('phone', '')}
        E-mail {data['deductor'].get('email', '')}

        4 Control totals
        Sr. No. 
        Return Type
        (Regular / Correction type)
        No. of deductee / party records
        Amount paid
        ( ₹ )
        Tax deducted / collected
        ( ₹ )
        Tax deposited
        (Total challan amount)
        ( ₹ )
        1 {data['form_details'].get('return_type', 'REGULAR')} {len(data['deductee_records'])} {data['control_totals'].get('amount_paid', '0.00')} {data['control_totals'].get('tax_deducted', '0.00')} {data['control_totals'].get('tax_deposited', '0.00')}
        Total {len(data['deductee_records'])} {data['control_totals'].get('amount_paid', '0.00')} {data['control_totals'].get('tax_deducted', '0.00')} {data['control_totals'].get('tax_deposited', '0.00')}

        5 Total Number of Annexures enclosed

        6 Other Information

        VERIFICATION
        I , {data['deductor'].get('responsible_person_name', '')} , hereby certify that all the particulars furnished above are correct and complete.

        Place: {data['deductor'].get('city', '')} Signature of person responsible for deducting / collecting tax at source
        Date: {current_date} Name and designation of person responsible for deducting / collecting tax at source {data['deductor'].get('responsible_person_name', '')}, {data['deductor'].get('designation', 'DIRECTOR')}

        * Mention type of deductor - Government or Others
        # dd/mm/yy :- date/month/year
        Generated by FVU Version 9.2"""
    
    return form_27a_content

@frappe.whitelist()
def generate_statistics_report(data):
    """Generate Statistics Report HTML"""
    # Calculate PAN statistics
    valid_pan_count = sum(1 for record in data['deductee_records']
                            if record.get('pan', '') and len(record.get('pan', '')) == 10)
    pan_applied_count = sum(1 for record in data['deductee_records']
                            if record.get('pan', '') == 'PANAPPLIED')
    pan_not_available_count = sum(1 for record in data['deductee_records']
                                    if record.get('pan', '') == 'PANNOTAVBL')
    pan_invalid_count = sum(1 for record in data['deductee_records']
                            if record.get('pan', '') == 'PANINVALID')
    
    html_content = f"""<HTML><HEAD> <TITLE> FVU -TDS STATEMENT STATISTICS REPORT </TITLE></HEAD>
        <BODY>
        <TABLE BORDER=1 BORDERCOLOR="000000" CELLSPACING=0 CELLPADDING=0 style='border-collapse: collapse; border: none; mso-border-alt: solid windowtext .5pt; mso-padding-alt: 0in 5.4pt 0in 5.4pt'>
        <TR><TD>
        <TABLE BORDER=0 BORDERCOLOR="000000" CELLSPACING=0 CELLPADDING=0 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD><BR><H3><CENTER> FVU -TDS STATEMENT STATISTICS REPORT - Batch Number 1</CENTER></H3></TD></TR>
        <TR><TD>You are advised to verify the details of your TAN at Income Tax Department's web-site (www.incometaxindia.gov.in) before submission of the statement. If the data displayed is not updated then request for necessary changes by submitting 'Form for Changes or Corrections in TAN data for TAN allotted' along with the statement.<BR><BR>The details in the report are as per the statement prepared by you. In case of any discrepancy in the details, rectify the statement accordingly. Thereafter, validate the rectified statement again through FVU.<BR><BR>The details provided in the physical Form 27A should match with the statistics report.<BR><BR>You can track the status of the challans as well as the statements furnished at www.tin-nsdl.com using TAN and Provisional Receipt Number.</TD></TR>
        </TABLE><BR><BR>

        <TABLE BORDER=.5pt CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD width=400 valign=top><B>   Name of Deductor </B></TD><TD width=200 valign=top><B>   TAN of Deductor </B></TD></TR>
        <TR><TD  ALIGN=LEFT width=500> {data['deductor'].get('name', '')}</TD><TD  ALIGN=LEFT width=250> {data['deductor'].get('tan', '')} </TD></TR>
        </TABLE>

        <P><TABLE BORDER=.5pt CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD width=250 valign=top><B>   PAN of Deductor </B></TD><TD valign=top><B>   Form Number  </B></TD><TD valign=top><B>   Form Type  </B></TD></TR>
        <TR><TD  ALIGN=LEFT width=250> {data['deductor'].get('pan', '')} </TD><TD  ALIGN=LEFT width=250> 24Q </TD><TD  ALIGN=LEFT width=250>Salary (Electronic)</TD></TR>
        </TABLE>

        <P><TABLE BORDER=1 CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD valign=top><B>   Assessment Year  </B></TD><TD valign=top><B>   Financial Year  </B></TD><TD valign=top><B>   Quarter  </B></TD><TD valign=top><B>   Upload Type  </B></TD><TD valign=top><B>   Type of Correction  </B></TD></TR>
        <TR><TD  ALIGN=LEFT width=150>{data['form_details'].get('assessment_year', '2026-27')} </TD><TD  ALIGN=LEFT width=150>{data['form_details'].get('financial_year', '2025-26')}</TD><TD  ALIGN=LEFT width=150>{data['form_details'].get('quarter', 'Q1')}</TD><TD  ALIGN=LEFT width=160>{data['form_details'].get('return_type', 'Regular')}</TD><TD  ALIGN=LEFT width=300>NA</TD></TR>
        </TABLE>

        <BR><TABLE BORDER=1 CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD valign=top width=200 style='text-align:left'><B> No. of Challans</B></TD><TD valign=top width=250 style='text-align:left'><B> Total Challan Amount (₹)</B></TD><TD valign=top width=150 style='text-align:left'><B> No. of Deductee Records</B></TD><TD valign=top width=200 style='text-align:left'><B> No. of Deductee Records where tax is deducted at Higher Rate</B></TD></TR>
        <TR><TD  ALIGN=RIGHT >{len(data['challan_details'])}</TD><TD  ALIGN=RIGHT >{data['control_totals'].get('tax_deposited', '0.00')}</TD><TD  ALIGN=RIGHT >{len(data['deductee_records'])}</TD><TD  ALIGN=RIGHT >0</TD></TR>
        </TABLE>

        <P><TABLE BORDER=1 CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD valign=top width=215 ><B> No. of Challans (excluding nil) </B></TD><TD valign=top width=215 ><B> No. of Unmatched challan </B></TD><TD valign=top width=215 ><B> No. of Matched challan </B></TD></TR>
        <TD  ALIGN=RIGHT >{len(data['challan_details'])}</TD><TD  ALIGN=RIGHT >{len(data['challan_details'])}</TD><TD  ALIGN=RIGHT >0</TD>
        </TABLE>

        <P><TABLE BORDER=1 CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD valign=top width=215 style='text-align:left'><B> Amount of Payment / Credit (₹)</B></TD><TD valign=top width=215 style='text-align:left'><B> Total Income Tax Deducted at Source (₹)</B></TD><TD valign=top width=215 style='text-align:left'><B> Total Tax Deposited as per Deductee Annexure (₹)</B></TD></TR>
        <TR><TD  ALIGN=RIGHT >{data['control_totals'].get('amount_paid', '0.00')}</TD><TD  ALIGN=RIGHT >{data['control_totals'].get('tax_deducted', '0.00')}</TD><TD  ALIGN=RIGHT >{data['control_totals'].get('tax_deposited', '0.00')}</TD></TR>
        </TABLE>

        <H4> Deductee PAN Details (Annexure I) </H4>
        <TABLE BORDER=1 CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD valign=top style='text-align:left'><B> No. of Valid PAN </B></TD><TD valign=top style='text-align:left'><B> No. of PAN Applied (PANAPPLIED)</B></TD><TD valign=top style='text-align:left'><B> No. of PAN Not Available (PANNOTAVBL)</B></TD><TD valign=top style='text-align:left'><B> No. of Structurally Invalid PAN (PANINVALID)</B></TD></TR>
        <TR><TD  ALIGN=RIGHT width=195>{valid_pan_count} </TD><TD  ALIGN=RIGHT width=189>{pan_applied_count} </TD><TD  ALIGN=RIGHT width=189>{pan_not_available_count} </TD><TD  ALIGN=RIGHT width=189>{pan_invalid_count} </TD></TR>
        </TABLE>

        <P><BR> FVU Version : 9.2 &nbsp;&nbsp; Input File Name : form24q.txt<BR><BR></TD></TR> 
        </TABLE><BR><BR><BR></BODY></HTML>"""
                
    return html_content

@frappe.whitelist()
def generate_warning_file(data):
    """Generate Warning File HTML"""
    html_content = """<HTML><HEAD> <TITLE> e-TDS/TCS statement warning file </TITLE></HEAD>
        <BODY><H3><CENTER><u> e-TDS/TCS statement warning file </u></CENTER></H3>
        <BR>e-TDS/TCS statement warning file is generated by FVU if :<BR>
        &nbsp &nbsp &nbsp &nbsp 1.	The value in the Bank Branch Code (BSR code) field of challan in the e-TDS/TCS statements is not present in the authorized list of collecting Bank Branch&nbsp &nbsp &nbsp &nbsp &nbsp &nbsp &nbsp Codes in the FVU and/or<BR>
        &nbsp &nbsp &nbsp &nbsp 2.	If the PAN of the deductor is same as that of any deductee in the e-TDS/TCS statement.<BR>
        &nbsp &nbsp &nbsp &nbsp 3.	If the challans details of the statement do not match with the details uploaded by the bank.<BR>
        &nbsp &nbsp &nbsp &nbsp 4.	In case tax is deducted at higher rate and corresponding rate of deduction is less than 20%.<BR>
        &nbsp &nbsp &nbsp &nbsp 5.	If date of deduction is beyond the quarter.<BR>
        &nbsp &nbsp &nbsp &nbsp 6.	If TAN name of the deductor is not present in TAN master of Income Tax Department (ITD).<BR>
        This file is generated to give an alert to the deductor about the records in which invalid values are mentioned.<BR><BR>

        <TABLE BORDER=1 CELLSPACING=0 CELLPADDING=0 BORDERCOLOR=000000 style='border-collapse:collapse; border:none;mso-border-alt:solid windowtext .5pt;mso-padding-alt:0in 5.4pt 0in 5.4pt'>
        <TR><TD width=70 valign=top style='text-align:left' ><B>   Line no. in the text file </B></TD><TD width=85 valign=top><B>   Record Type </B></TD><TD width=85 valign=top><B>   Batch no. in the text file</B></TD><TD width=85 valign=top><B>   Challan detail record no. </B></TD><TD width=85 valign=top><B>   Deductee/ Salary detail record no. </B></TD><TD width=90 valign=top><B>   Challan tender date </B></TD><TD width=90 valign=top><B>   Challan Serial no. </B></TD><TD width=90 valign=top><B>   BSR code </B></TD><TD width=95 valign=top><B>   Error Code </B></TD><TD width=585 valign=top><B>   Error Description </B></TD></TR>"""
    
    # Add warning rows based on challan details
    for i, challan in enumerate(data['challan_details'], 1):
        html_content += f"""<TR><TD  ALIGN=RIGHT width=70> {i*100+3}</TD><TD  ALIGN=LEFT width=85> Challan </TD><TD  ALIGN=RIGHT width=85> 1 </TD><TD  ALIGN=RIGHT width=85> {i} </TD><TD  ALIGN=RIGHT width=85> NA </TD><TD  ALIGN=LEFT width=85> {challan.get('tender_date', '30/04/2025')} </TD><TD  ALIGN=RIGHT width=85> {challan.get('serial_number', '12345')} </TD><TD  ALIGN=RIGHT width=85> {challan.get('bsr_code', '6390009')} </TD><TD  ALIGN=LEFT width=90> T-FV-3141 </TD><TD  ALIGN=LEFT width=585> Challan details mentioned in the statement not present in the challan file imported  </TD></TR>"""
    
    html_content += """</TABLE><BR><BR>

            <B>Bank branch code not present in the list of authorized bank branches:</B><BR>
            <P>The Bank Branch Code is provided on the challan counterfoil along with the tender date and challan serial no. by the collecting bank branch where TDS / TCS has been deposited.<BR>
            Deductor / Collector should verify the Bank Branch Code mentioned in the e-TDS/TCS statement with the bank branch code on the challan counterfoil provided by the bank.<BR>
            In case of mismatch, the bank branch codes as per the challan counterfoil should be mentioned in the e-TDS/TCS statement and the file should be revalidated through FVU.<BR>
            In case there is no mismatch then the .fvu file created by the FVU should be submitted to the TIN-FC. </P><BR>

            <P><B>Same PAN in deductor and deductee PAN field.</P></B><P>PAN of the deductor given in the deductor details should normally not appear in the deductee details.<BR>Deductor/Collector should verify the PAN in the deductee details and if the same has been correctly entered, then the .fvu file created by the FVU should be submitted to the TIN-FC.</P><BR>

            FVU Version : 9.2 &nbsp;&nbsp; Input File Name : form24q.txt<BR><BR><BR></BODY></HTML>"""
    
    return html_content

@frappe.whitelist()
def generate_fvu_xml(data):
    """Generate FVU XML file"""
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Form24Q>
            <Header>
                <FormType>24Q</FormType>
                <AssessmentYear>{data['form_details'].get('assessment_year', '2026-27')}</AssessmentYear>
                <FinancialYear>{data['form_details'].get('financial_year', '2025-26')}</FinancialYear>
                <Quarter>{data['form_details'].get('quarter', 'Q1')}</Quarter>
                <PANofDeductor>{data['deductor'].get('pan', '')}</PANofDeductor>
                <TANofDeductor>{data['deductor'].get('tan', '')}</TANofDeductor>
                <DeductorName>{data['deductor'].get('name', '')}</DeductorName>
                <DateofGeneration>{nowdate()}</DateofGeneration>
            </Header>

            <ChallanDetails>"""
    
    for i, challan in enumerate(data['challan_details'], 1):
        xml_content += f"""
                <Challan{i}>
                    <TenderDate>{challan.get('tender_date', '')}</TenderDate>
                    <SerialNumber>{challan.get('serial_number', '')}</SerialNumber>
                    <BSRCode>{challan.get('bsr_code', '')}</BSRCode>
                    <Amount>{challan.get('amount', '0.00')}</Amount>
                </Challan{i}>"""
    
    xml_content += """
            </ChallanDetails>

            <DeducteeRecords>"""
    
    for i, deductee in enumerate(data['deductee_records'], 1):
        xml_content += f"""
                <Record{i}>
                    <PAN>{deductee.get('pan', '')}</PAN>
                    <Name>{deductee.get('name', '')}</Name>
                    <AmountPaid>{deductee.get('amount_paid', '0.00')}</AmountPaid>
                    <TaxDeducted>{deductee.get('tax_deducted', '0.00')}</TaxDeducted>
                    <DateOfDeduction>{deductee.get('date_of_deduction', '')}</DateOfDeduction>
                </Record{i}>"""
    
    xml_content += f"""
            </DeducteeRecords>

            <Summary>
                <TotalRecords>{len(data['deductee_records'])}</TotalRecords>
                <TotalChallans>{len(data['challan_details'])}</TotalChallans>
                <TotalAmountPaid>{data['control_totals'].get('amount_paid', '0.00')}</TotalAmountPaid>
                <TotalTaxDeducted>{data['control_totals'].get('tax_deducted', '0.00')}</TotalTaxDeducted>
            </Summary>
        </Form24Q>"""
    
    return xml_content

@frappe.whitelist()
def generate_text_file(data):
    """Generate text file for FVU"""
    text_content = f"""FH|FILE HEADER|{data['deductor'].get('tan', '')}|{data['form_details'].get('financial_year', '2025-26')}|{data['form_details'].get('quarter', 'Q1')}|24Q|1.0|{nowdate()}|ORIGINAL|{len(data['deductee_records'])}|{data['control_totals'].get('amount_paid', '0.00')}|{data['control_totals'].get('tax_deducted', '0.00')}

BH|BATCH HEADER|1|{data['deductor'].get('tan', '')}|{data['deductor'].get('pan', '')}|{data['deductor'].get('name', '')}|{data['form_details'].get('assessment_year', '2026-27')}|{data['form_details'].get('quarter', 'Q1')}"""
    
    # Add challan details
    for i, challan in enumerate(data['challan_details'], 1):
        text_content += f"""
CH|{challan.get('tender_date', '')}|{challan.get('serial_number', '')}|{challan.get('bsr_code', '')}|{challan.get('amount', '0.00')}|0.00|{challan.get('amount', '0.00')}|{i}"""
    
    # Add deductee details
    for i, deductee in enumerate(data['deductee_records'], 1):
        text_content += f"""
DH|{i}|{deductee.get('pan', '')}|{deductee.get('name', '')}|{deductee.get('amount_paid', '0.00')}|{deductee.get('tax_deducted', '0.00')}|{deductee.get('date_of_deduction', '')}|192A|10.00|N"""
    
    text_content += f"""

BT|{len(data['challan_details'])}|{len(data['deductee_records'])}|{data['control_totals'].get('amount_paid', '0.00')}|{data['control_totals'].get('tax_deducted', '0.00')}

FT|1|{len(data['challan_details'])}|{len(data['deductee_records'])}|{data['control_totals'].get('amount_paid', '0.00')}|{data['control_totals'].get('tax_deducted', '0.00')}"""
    
    return text_content

@frappe.whitelist()
def save_generated_files(files_data, parsed_data):
    """Save generated files to site files directory"""
    file_paths = {}
    
    try:
        # Create directory structure
        base_path = get_site_path('public', 'files', 'fvu_generated')
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        
        # Generate file names
        tan = parsed_data['deductor'].get('tan', 'TAN')
        quarter = parsed_data['form_details'].get('quarter', 'Q1')
        financial_year = parsed_data['form_details'].get('financial_year', '202526')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean financial year (remove hyphen)
        fy_clean = financial_year.replace('-', '')
        
        # File name mappings
        file_configs = {
            'form_27a': {
                'filename': f'27A_{tan}_24Q_{quarter}_{fy_clean}.pdf',
                'content': files_data['form_27a'],
                'content_type': 'text/plain'
            },
            'statistics_report': {
                'filename': f'form24q.html',
                'content': files_data['statistics_report'],
                'content_type': 'text/html'
            },
            'warning_file': {
                'filename': f'form24q_Electronic_Statement_Warning_File.html',
                'content': files_data['warning_file'],
                'content_type': 'text/html'
            },
            'fvu_file': {
                'filename': f'form24q.fvu',
                'content': files_data['fvu_file'],
                'content_type': 'application/xml'
            },
            'text_file': {
                'filename': f'form24q.txt',
                'content': files_data['text_file'],
                'content_type': 'text/plain'
            }
        }
        
        # Save each file
        for file_key, config in file_configs.items():
            try:
                file_path = os.path.join(base_path, config['filename'])
                
                # Write file content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(config['content'])
                
                # Create File document in Frappe
                file_doc = frappe.get_doc({
                    'doctype': 'File',
                    'file_name': config['filename'],
                    'file_url': f'/files/fvu_generated/{config["filename"]}',
                    'folder': 'Home/Attachments',
                    'is_private': 0,
                    'file_size': len(config['content'].encode('utf-8')),
                    'content_type': config['content_type']
                })
                file_doc.insert(ignore_permissions=True)
                
                # Store file path info
                file_paths[file_key] = {
                    'filename': config['filename'],
                    'file_url': file_doc.file_url,
                    'file_path': file_path,
                    'file_doc_name': file_doc.name,
                    'size': file_doc.file_size,
                    'content_type': config['content_type']
                }
                
                frappe.logger().info(f"Generated FVU file: {config['filename']}")
                
            except Exception as file_error:
                frappe.logger().error(f"Error saving file {config['filename']}: {str(file_error)}")
                file_paths[file_key] = {
                    'error': str(file_error),
                    'filename': config['filename']
                }
        
        # Create a summary log file
        summary_content = f"""FVU File Generation Summary
==========================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
TAN: {tan}
Quarter: {quarter}
Financial Year: {financial_year}
Assessment Year: {parsed_data['form_details'].get('assessment_year', '2026-27')}

Files Generated:
"""
        
        for file_key, file_info in file_paths.items():
            if 'error' not in file_info:
                summary_content += f"✓ {file_info['filename']} ({file_info['size']} bytes)\n"
            else:
                summary_content += f"✗ {file_info['filename']} - Error: {file_info['error']}\n"
        
        summary_content += f"""
Statistics:
-----------
Total Deductees: {len(parsed_data['deductee_records'])}
Total Challans: {len(parsed_data['challan_details'])}
Total Amount Paid: ₹{parsed_data['control_totals'].get('amount_paid', '0.00')}
Total Tax Deducted: ₹{parsed_data['control_totals'].get('tax_deducted', '0.00')}
Total Tax Deposited: ₹{parsed_data['control_totals'].get('tax_deposited', '0.00')}
"""
        
        # Save summary file
        summary_filename = f'FVU_Summary_{tan}_{quarter}_{timestamp}.log'
        summary_path = os.path.join(base_path, summary_filename)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        # Create summary File document
        summary_doc = frappe.get_doc({
            'doctype': 'File',
            'file_name': summary_filename,
            'file_url': f'/files/fvu_generated/{summary_filename}',
            'folder': 'Home/Attachments',
            'is_private': 0,
            'file_size': len(summary_content.encode('utf-8')),
            'content_type': 'text/plain'
        })
        summary_doc.insert(ignore_permissions=True)
        
        file_paths['summary'] = {
            'filename': summary_filename,
            'file_url': summary_doc.file_url,
            'file_path': summary_path,
            'file_doc_name': summary_doc.name,
            'size': summary_doc.file_size,
            'content_type': 'text/plain'
        }
        
        frappe.db.commit()
        return file_paths
        
    except Exception as e:
        frappe.logger().error(f"Error in save_generated_files: {str(e)}")
        frappe.throw(f"Failed to save generated files: {str(e)}")

@frappe.whitelist()
def cleanup_old_fvu_files(days_old=30):
    """Clean up old FVU generated files"""
    try:
        base_path = get_site_path('public', 'files', 'fvu_generated')
        if not os.path.exists(base_path):
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for filename in os.listdir(base_path):
            file_path = os.path.join(base_path, filename)
            if os.path.isfile(file_path):
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_modified_time < cutoff_date:
                    try:
                        # Remove file from filesystem
                        os.remove(file_path)
                        
                        # Remove File document from Frappe
                        file_url = f'/files/fvu_generated/{filename}'
                        file_docs = frappe.get_all('File', filters={'file_url': file_url})
                        
                        for file_doc in file_docs:
                            frappe.delete_doc('File', file_doc.name, ignore_permissions=True)
                        
                        frappe.logger().info(f"Cleaned up old FVU file: {filename}")
                        
                    except Exception as cleanup_error:
                        frappe.logger().error(f"Error cleaning up file {filename}: {str(cleanup_error)}")
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.logger().error(f"Error in cleanup_old_fvu_files: {str(e)}")

@frappe.whitelist()
def get_fvu_download_links(file_paths):
    """Get formatted download links for generated FVU files"""
    download_links = []
    
    for file_key, file_info in file_paths.items():
        if 'error' not in file_info:
            download_links.append({
                'label': get_file_label(file_key),
                'url': file_info['file_url'],
                'filename': file_info['filename'],
                'size': file_info['size'],
                'type': file_info['content_type']
            })
    
    return download_links

@frappe.whitelist()
def get_file_label(file_key):
    """Get user-friendly labels for file types"""
    labels = {
        'form_27a': 'Form 27A (PDF Format)',
        'statistics_report': 'Statistics Report (HTML)',
        'warning_file': 'Warning File (HTML)',
        'fvu_file': 'FVU File (XML)',
        'text_file': 'Text File (TXT)',
        'summary': 'Generation Summary (LOG)'
    }
    return labels.get(file_key, file_key.replace('_', ' ').title())