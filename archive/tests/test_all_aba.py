import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from banks.aba import extract_aba_statement

pdf_dir = 'Test'
for file in os.listdir(pdf_dir):
    if file.startswith('ABA') and file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_dir, file)
        out_path = os.path.join(pdf_dir, file.replace('.pdf', '_out.csv'))
        print(f"\n--- Testing {file} ---")
        try:
            extract_aba_statement(pdf_path, out_path, include_summary=True)
            print(f"Success: {file}")
        except Exception as e:
            print(f"FAILED on {file}: {e}")
