import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from banks.aba import extract_aba_statement
pdf_path = r'd:\Programming\web-converter\Test\ABA 262.pdf'
out_path = 'debug2.csv'

extract_aba_statement(pdf_path, out_path, include_summary=False)

df = pd.read_csv(out_path, dtype=str)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
print(df[['TRANSACTION DETAILS', 'MONEY IN', 'MONEY OUT']].head(10))
