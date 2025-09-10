#!/usr/bin/env python3
import sys
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec

def sign_pdf_single(input_path, output_path, cert_path, password, signer_name, designation, location):
    """Original single signature for Form A"""
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=cert_path,
        passphrase=password.encode('utf-8')
    )
    
    with open(input_path, 'rb') as input_file:
        writer = IncrementalPdfFileWriter(input_file)
        
        # Position signature in the signature area on page 2
        sig_field_spec = SigFieldSpec(
            'Signature',
            on_page=1,  # Page 2 (0-indexed)
            box=(300, 490, 550, 520)
        )
        
        out = signers.sign_pdf(
            writer,
            signature_meta=signers.PdfSignatureMetadata(
                field_name='Signature',
                location=location,
                reason=f'Form 16 Digital Signature',
                name=f'{signer_name}, {designation}'
            ),
            signer=signer,
            new_field_spec=sig_field_spec
        )
        
        with open(output_path, 'wb') as output_file:
            output_file.write(out.getvalue())

def sign_pdf_multiple(input_path, output_path, cert_path, password, signer_name, designation, location):
    """Multiple signatures for Form B - pages 3 and 4"""
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=cert_path,
        passphrase=password.encode('utf-8')
    )
    
    # Define signature positions for pages 3 and 4 (bottom of pages)
    signature_configs = [
        {
            'field_name': 'Signature_Page3',
            'page': 2,  # Page 3 
            'box': (335, 100, 575, 130),  
            'reason': 'Form 16 Part B Digital Signature - Page 3'
        },
        {
            'field_name': 'Signature_Page4', 
            'page': 3,  # Page 4 
            'box': (335, 380, 575, 410),
            'reason': 'Form 16 Part B Digital Signature - Page 4'
        }
    ]

    
    with open(input_path, 'rb') as input_file:
        writer = IncrementalPdfFileWriter(input_file)
        
        # Add first signature
        first_config = signature_configs[0]
        sig_field_spec = SigFieldSpec(
            first_config['field_name'],
            on_page=first_config['page'],
            box=first_config['box']
        )
        
        out = signers.sign_pdf(
            writer,
            signature_meta=signers.PdfSignatureMetadata(
                field_name=first_config['field_name'],
                location=location,
                reason=first_config['reason'],
                name=f'{signer_name}, {designation}'
            ),
            signer=signer,
            new_field_spec=sig_field_spec
        )
        
        # For subsequent signatures, we need to work with the already signed PDF
        temp_output = output_path + '.tmp'
        with open(temp_output, 'wb') as temp_file:
            temp_file.write(out.getvalue())
        
        # Add remaining signatures
        for config in signature_configs[1:]:
            with open(temp_output, 'rb') as signed_file:
                writer = IncrementalPdfFileWriter(signed_file)
                
                sig_field_spec = SigFieldSpec(
                    config['field_name'],
                    on_page=config['page'],
                    box=config['box']
                )
                
                out = signers.sign_pdf(
                    writer,
                    signature_meta=signers.PdfSignatureMetadata(
                        field_name=config['field_name'],
                        location=location,
                        reason=config['reason'],
                        name=f'{signer_name}, {designation}'
                    ),
                    signer=signer,
                    new_field_spec=sig_field_spec
                )
                
                with open(temp_output, 'wb') as temp_file:
                    temp_file.write(out.getvalue())
        
        # Move final result to output path
        import os
        os.rename(temp_output, output_path)

if __name__ == "__main__":
    if len(sys.argv) < 8:
        print("Usage: python3 sign_pdfs.py <input_pdf> <output_pdf> <cert_path> <password> <signer_name> <designation> <location> [part_type]")
        sys.exit(1)
    
    part_type = sys.argv[8] if len(sys.argv) > 8 else "PartA"
    
    if part_type == "PartB":
        sign_pdf_multiple(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], 
                         sys.argv[5], sys.argv[6], sys.argv[7])
    else:
        sign_pdf_single(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], 
                       sys.argv[5], sys.argv[6], sys.argv[7])