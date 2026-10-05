import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

pdf_path = r'd:\Programming\web-converter\Test\ABA 262.pdf'
out_path = r'd:\Programming\web-converter\Test\ABA 262_debug.csv'

df = pd.read_csv(out_path)
pd.set_option('display.max_columns', None)
print(df[['MONEY IN', 'MONEY OUT', 'BALANCE']].head(15))
