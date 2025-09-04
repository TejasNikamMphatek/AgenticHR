#!/usr/bin/env python3
import sys
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec

def sign_pdf(input_path, output_path, cert_path, password, signer_name, designation, location):
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
            # box=(300, 520, 50, 490)  # Signature box coordinates
            box = (300, 490, 550, 520)

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

if __name__ == "__main__":
    sign_pdf(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], 
             sys.argv[5], sys.argv[6], sys.argv[7])