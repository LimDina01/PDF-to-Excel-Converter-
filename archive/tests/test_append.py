import os
import django
import pdfplumber
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

pdf_path = r'd:\Programming\web-converter\Test\ABA 262.pdf'

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
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
    
    has_started_transactions = False
    current_row = None
    rows = []
    
    for line in lines:
        if not line:
            continue
            
        line_text = " ".join([w['text'] for w in line])
        
        if not has_started_transactions:
            if "Date Transaction Details Money In Money Out Balance" in line_text or \
               "Date Description Money In Money Out Balance" in line_text or \
               "Date Transaction Type Transaction Details Money In Money Out Balance" in line_text:
                has_started_transactions = True
            continue
            
        is_new_row = False
        if len(line) >= 3:
            if line[0]['x0'] < 90:
                date_str = f"{line[0]['text']} {line[1]['text']} {line[2]['text']}"
                if re.match(r'^\d{2} [A-Z][a-z]{2} \d{4}$', date_str) or re.match(r'^[A-Z][a-z]{2} \d{2}, \d{4}$', date_str):
                    is_new_row = True
                    has_started_transactions = True
        
        is_summary_row = False
        
        if is_new_row or is_summary_row:
            if current_row:
                rows.append(current_row)
                if len(rows) == 1:
                    print("FIRST ROW APPENDED:", current_row)
                    break
                    
            current_row = {
                'VALUE DATE': '',
                'TRANSACTION DETAILS': '',
                'MONEY IN': '',
                'MONEY OUT': '',
                'BALANCE': ''
            }
            
            for w in line:
                x = w['x0']
                text = w['text']
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
