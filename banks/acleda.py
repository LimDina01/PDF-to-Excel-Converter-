import pdfplumber
import pandas as pd
import re
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

def extract_acleda_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading ACLEDA PDF: {pdf_path}")
    
    rows = []
    current_row = None
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            if progress_callback:
                progress_callback(i + 1, total_pages)
            print(f"Extracting page {i + 1}...")
            
            words = page.extract_words()
            if not words:
                continue
                
            words.sort(key=lambda w: (w['top'], w['x0']))
            lines = []
            current_line = []
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
                
                if 'Page:' in line_text or 'DATE DESCRIPTIONS' in line_text or 'ACCOUNT STATEMENT' in line_text or 'FROM ' in line_text or 'ACCOUNT INFORMATION' in line_text or 'Account name :' in line_text or 'Account number :' in line_text or 'Currency :' in line_text or 'Account type :' in line_text or 'SWIFT code :' in line_text or 'TRANSACTION DETAILS' in line_text or 'A CLEDA BANK PLC.' in line_text or 'Address :' in line_text or 'ENDING BALANCE' in line_text or 'The transactions shown above' in line_text or 'DISCLAIMER:' in line_text or 'with seal.' in line_text:
                    continue
                    
                is_new_row = False
                if len(line) >= 3:
                    date_str = f"{line[0]['text']} {line[1]['text']} {line[2]['text']}"
                    if re.match(r'^[A-Z][a-z]{2} \d{1,2}, \d{4}$', date_str):
                        is_new_row = True
                        
                if is_new_row:
                    if current_row:
                        rows.append(current_row)
                        
                    current_row = {
                        'DATE': '',
                        'DESCRIPTIONS': '',
                        'CASH OUT (Dr)': '',
                        'CASH IN (Cr)': '',
                        'BALANCE': ''
                    }
                    
                    for w in line:
                        x = w['x0']
                        text = w['text']
                        if x < 80:
                            current_row['DATE'] += text + ' '
                        elif x < 320:
                            current_row['DESCRIPTIONS'] += text + ' '
                        elif x < 420:
                            current_row['CASH OUT (Dr)'] += text + ' '
                        elif x < 510:
                            current_row['CASH IN (Cr)'] += text + ' '
                        else:
                            current_row['BALANCE'] += text + ' '
                else:
                    if current_row:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            if x < 320:
                                current_row['DESCRIPTIONS'] += text + ' '
                            elif x < 420:
                                current_row['CASH OUT (Dr)'] += text + ' '
                            elif x < 510:
                                current_row['CASH IN (Cr)'] += text + ' '
                            else:
                                current_row['BALANCE'] += text + ' '

    if current_row:
        rows.append(current_row)
    
    if not rows:
        print("No transactions found in the PDF. Generating empty statement.")
        df = pd.DataFrame(columns=['DATE', 'DESCRIPTIONS', 'CASH OUT (Dr)', 'CASH IN (Cr)', 'BALANCE'])
    else:
        df = pd.DataFrame(rows)
        
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        # Remove illegal XML characters to prevent openpyxl crashes
        df[col] = df[col].apply(lambda val: ILLEGAL_CHARACTERS_RE.sub('', val) if isinstance(val, str) else val)
        
    if 'DATE' in df.columns and not df.empty:
        df['DATE'] = pd.to_datetime(df['DATE'], format='%b %d, %Y', errors='coerce')

    for col in ['CASH OUT (Dr)', 'CASH IN (Cr)', 'BALANCE']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'CASH IN (Cr)' in df.columns and 'CASH OUT (Dr)' in df.columns:
        df['Statement Amount'] = df['CASH IN (Cr)'].fillna(0) - df['CASH OUT (Dr)'].fillna(0)

    df.to_csv(output_path, index=False, encoding='utf-8-sig', float_format='%.2f', lineterminator='\r\n')
    
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD MMM YYYY') as writer:
        df.to_excel(writer, index=False)
    
    print(f"Successfully converted ACLEDA! Total transactions extracted: {len(df)}")
    return True
