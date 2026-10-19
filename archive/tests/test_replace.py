import pandas as pd
import re
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

rows = [
    {
        'VALUE DATE': 'Sep 01, 2026 ',
        'TRANSACTION DETAILS': 'INTEREST PAYMENT FOR LOAN # ON Aug 31, 2026 11:33 PM REF# 101IC01USD000001 ',
        'MONEY IN': '',
        'MONEY OUT': '12,030.71 USD ',
        'BALANCE': '-2,568,053.45 USD '
    }
]

df = pd.DataFrame(rows)

def clean_illegal_chars(val):
    if isinstance(val, str):
        return ILLEGAL_CHARACTERS_RE.sub('', val)
    return val

for col in df.columns:
    df[col] = df[col].apply(clean_illegal_chars)

print("Before replace:")
print(df[['MONEY IN', 'MONEY OUT']].values)

for col in ['MONEY IN', 'MONEY OUT', 'BALANCE']:
    if col in df.columns:
        df[col] = df[col].replace(' USD', '', regex=True)
        df[col] = df[col].replace(' KHR', '', regex=True)
        
        print(f"After USD/KHR replace for {col}:")
        print(df[col].values)
        
        df[col] = df[col].replace('', '0.00').replace(',', '', regex=True)
        
        print(f"After empty/comma replace for {col}:")
        print(df[col].values)
        
        df[col] = pd.to_numeric(df[col], errors='coerce')

print("\nFinal df:")
print(df[['MONEY IN', 'MONEY OUT', 'BALANCE']])
