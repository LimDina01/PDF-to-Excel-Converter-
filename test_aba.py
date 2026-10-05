import pdfplumber
import pandas as pd
import re
import os

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"

rows = []
current_row = None
has_started_transactions = False
seen_table_headers = False

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages[:2]:
        words = page.extract_words()
        words.sort(key=lambda w: (w['top'], w['x0']))
        
        lines = []
        current_line = []
        if words:
            current_top = words[0]['top']
            for w in words:
                if abs(w['top'] - current_top) > 3:
                    current_line.sort(key=lambda x: x['x0'])
                    lines.append(current_line)
                    current_line = [w]
                    current_top = w['top']
                else:
                    current_line.append(w)
            if current_line:
                current_line.sort(key=lambda x: x['x0'])
                lines.append(current_line)

        for line in lines:
            line_text = " ".join([w['text'] for w in line])
            if 'Generated on:' in line_text or 'DISCLAIMER:' in line_text or 'Page ' in line_text or 'Advanced Bank of Asia' in line_text or 'ACCOUNT STATEMENT' in line_text:
                continue
                
            if 'Date Transaction Details' in line_text or ('TRANSACTION TYPE' in line_text):
                seen_table_headers = True
                continue
            
            is_new_row = False
            # Check for Mmm DD, YYYY
            if len(line) >= 3:
                date_str = f"{line[0]['text']} {line[1]['text']} {line[2]['text']}"
                if re.match(r'^[A-Z][a-z]{2} \d{2}, \d{4}$', date_str) or re.match(r'^\d{2} [A-Z][a-z]{2} \d{4}$', date_str):
                    is_new_row = True
                    has_started_transactions = True
            
            is_summary_row = False
            if line_text.startswith("Opening Balance") and "Total" not in line_text and seen_table_headers:
                is_summary_row = True
            elif has_started_transactions:
                if line_text.startswith("Ending Balance") or line_text.startswith("Total Money In") or line_text.startswith("Total Money Out") or line_text.startswith("Credit Balance") or line_text.startswith("Closing Balance") or line_text.startswith("Total Blocked Amounts") or line_text.startswith("Blocked Amounts"):
                    is_summary_row = True
                elif line_text.startswith("Balance ") or line_text == "Balance":
                    is_summary_row = True
            
            if is_new_row or is_summary_row:
                if current_row:
                    rows.append(current_row)
                    
                current_row = {
                    'VALUE DATE': '',
                    'TRANSACTION TYPE': '',
                    'TRANSACTION DETAILS': '',
                    'MONEY IN': '',
                    'MONEY OUT': '',
                    'BALANCE': ''
                }
                
                if is_summary_row:
                    for w in line:
                        x = w['x0']
                        text = w['text']
                        if x > 400 and bool(re.search(r'\d', text)):
                            current_row['BALANCE'] += text + ' '
                        else:
                            current_row['TRANSACTION DETAILS'] += text + ' '
                else:
                    for w in line:
                        x = w['x0']
                        text = w['text']
                        # New Logic
                        if x < 90:
                            current_row['VALUE DATE'] += text + ' '
                        elif x < 320:
                            current_row['TRANSACTION DETAILS'] += text + ' '
                        elif x < 390:
                            current_row['MONEY IN'] += text + ' '
                        elif x < 460:
                            current_row['MONEY OUT'] += text + ' '
                        else:
                            current_row['BALANCE'] += text + ' '
            else:
                if current_row:
                    for w in line:
                        x = w['x0']
                        text = w['text']
                        if 90 <= x < 320:
                            current_row['TRANSACTION DETAILS'] += text + ' '
                        elif x < 90:
                            current_row['VALUE DATE'] += text + ' '

if current_row:
    rows.append(current_row)

df = pd.DataFrame(rows)
print(df.head(15))
