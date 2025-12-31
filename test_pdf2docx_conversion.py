#!/usr/bin/env python3
"""
Test script to verify pdf2docx conversion works correctly
This script tests the new pdf2docx-based conversion locally before deploying to Railway
"""

import os
import sys
import tempfile
from pdf2docx import Converter

def test_conversion():
    """Test basic PDF to DOCX conversion"""
    
    # Create a simple test PDF
    test_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World - Test PDF to DOCX Conversion) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000240 00000 n 
0000000377 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
448
%%EOF"""
    
    print("=" * 60)
    print("TEST: PDF to DOCX Conversion with pdf2docx")
    print("=" * 60)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save test PDF
        pdf_path = os.path.join(temp_dir, "test.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(test_pdf)
        
        print(f"\n✓ Test PDF created: {pdf_path}")
        print(f"  Size: {len(test_pdf)} bytes")
        
        # Convert to DOCX
        docx_path = os.path.join(temp_dir, "test.docx")
        
        print(f"\n⏳ Converting to DOCX...")
        try:
            cv = Converter(pdf_path)
            cv.convert(docx_path, start=0, end=None)
            cv.close()
            
            # Check if DOCX was created
            if os.path.exists(docx_path):
                with open(docx_path, 'rb') as f:
                    docx_content = f.read()
                
                print(f"✓ Conversion successful!")
                print(f"  Output: {docx_path}")
                print(f"  Size: {len(docx_content)} bytes")
                print(f"  Valid DOCX: {docx_content.startswith(b'PK')}")
                print("\n" + "=" * 60)
                print("✅ TEST PASSED: pdf2docx is working correctly")
                print("=" * 60)
                return True
            else:
                print(f"✗ Conversion failed: DOCX file not created")
                print("\n" + "=" * 60)
                print("❌ TEST FAILED")
                print("=" * 60)
                return False
                
        except Exception as e:
            print(f"✗ Conversion failed with error: {e}")
            print("\n" + "=" * 60)
            print("❌ TEST FAILED")
            print("=" * 60)
            return False

if __name__ == "__main__":
    success = test_conversion()
    sys.exit(0 if success else 1)
