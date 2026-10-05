import pdfplumber
import pandas as pd
import re
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

def extract_ftb_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading FTB PDF: {pdf_path}")
    
    rows = []
    current_row = None
    
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = pdf.pages[0].extract_text() or ""
        is_overdraft_layout = 'OVERDRAFT ACCOUNT STATEMENT' in first_page_text
        
        # Default boundaries based on layout
        col_bounds = {
            'desc_end': 190 if is_overdraft_layout else 250,
            'ref_end': 300 if is_overdraft_layout else 355,
            'out_end': 400 if is_overdraft_layout else 430,
            'in_end': 500 if is_overdraft_layout else 500
        }
        
        # Dynamic Header Anchoring (read from page 1)
        words = pdf.pages[0].extract_words()
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
                lines.append(current_line)
                
            for line in lines:
                line_text = " ".join([w['text'] for w in line])
                if 'Description' in line_text and 'Reference' in line_text and 'Balance' in line_text:
                    desc_word = next((w for w in line if 'Description'.lower() in w['text'].lower()), None)
                    ref_word = next((w for w in line if 'Reference'.lower() in w['text'].lower()), None)
                    out_word = next((w for w in line if 'Out'.lower() in w['text'].lower()), None)
                    in_word = next((w for w in line if 'In'.lower() == w['text'].lower()), None)
                    
                    if ref_word and out_word:
                        col_bounds['desc_end'] = (desc_word['x1'] + ref_word['x0']) / 2 if desc_word else ref_word['x0'] - 20
                        col_bounds['ref_end'] = (ref_word['x1'] + out_word['x0']) / 2
                    if out_word and in_word:
                        col_bounds['out_end'] = (out_word['x1'] + in_word['x0']) / 2
                    if in_word:
                        balance_word = next((w for w in line if 'Balance'.lower() in w['text'].lower()), None)
                        if balance_word:
                            col_bounds['in_end'] = (in_word['x1'] + balance_word['x0']) / 2
                    break
                    
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
                
                if 'Page ' in line_text or 'OVERDRAFT ACCOUNT STATEMENT' in line_text or 'ACCOUNT STATEMENT' in line_text or 'From Date' in line_text or 'Printed On' in line_text or 'User :' in line_text or 'Account Detail' in line_text or 'Customer ID' in line_text or 'Customer Name' in line_text or 'Account Number' in line_text or 'Customer Number' in line_text or 'Overdraft Loan ID' in line_text or 'Currency ' in line_text or 'Address ' in line_text or 'Account Activities' in line_text or 'Trn Date Description' in line_text or 'Detailed Account Credit' in line_text or 'Charge Debit Detailed Account' in line_text or ('Credit' in line_text and len(line) == 1) or 'This statement is computer generated' in line_text or 'not require signature' in line_text or 'Building No.' in line_text or 'Vong, Khan' in line_text or 'receipt, otherwise' in line_text or 'Email : customercare' in line_text or 'Cambodia Tel' in line_text or 'Total ' in line_text or 'Website:' in line_text:
                    continue
                
                if not include_summary and ('Closing Balance' in line_text or 'Ending Balance' in line_text or 'Opening Balance' in line_text):
                    continue
                    
                is_summary_row = False
                if include_summary:
                    if 'Opening Balance' in line_text or 'Closing Balance' in line_text or 'Ending Balance' in line_text:
                        is_summary_row = True
                        
                is_new_row = False
                if len(line) >= 1:
                    date_str = line[0]['text']
                    if re.match(r'^\d{2}-[a-zA-Z]{3}-\d{4}$', date_str):
                        is_new_row = True
                        
                if is_new_row or is_summary_row:
                    if current_row:
                        rows.append(current_row)
                        
                    current_row = {
                        'Trn Date': '',
                        'Description': '',
                        'Trn Reference': '',
                        'Cash Out': '',
                        'Cash In': '',
                        'Balance': ''
                    }
                    
                    if is_summary_row:
                        for w in line:
                            x0 = w['x0']
                            x1 = w['x1']
                            text = w['text']
                            if x1 < col_bounds['ref_end']:
                                current_row['Description'] += text + ' '
                            elif x1 < col_bounds['out_end']:
                                current_row['Cash Out'] += text + ' '
                            elif x1 < col_bounds['in_end']:
                                current_row['Cash In'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '
                    else:
                        for w in line:
                            x0 = w['x0']
                            x1 = w['x1']
                            text = w['text']
                            
                            if x1 < 80:
                                current_row['Trn Date'] += text + ' '
                            else:
                                if x1 < col_bounds['ref_end']:
                                    if x0 < col_bounds['desc_end']:
                                        current_row['Description'] += text + ' '
                                    else:
                                        current_row['Trn Reference'] += text + ' '
                                elif x1 < col_bounds['out_end']:
                                    current_row['Cash Out'] += text + ' '
                                elif x1 < col_bounds['in_end']:
                                    current_row['Cash In'] += text + ' '
                                else:
                                    current_row['Balance'] += text + ' '
                else:
                    if current_row:
                        for w in line:
                            x0 = w['x0']
                            x1 = w['x1']
                            text = w['text']
                            if x1 < col_bounds['ref_end']:
                                if x0 < col_bounds['desc_end']:
                                    current_row['Description'] += text + ' '
                                else:
                                    current_row['Trn Reference'] += text + ' '
                            elif x1 < col_bounds['out_end']:
                                current_row['Cash Out'] += text + ' '
                            elif x1 < col_bounds['in_end']:
                                current_row['Cash In'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '

    if current_row:
        rows.append(current_row)
    
    if not rows:
        print("No transactions found in the PDF. Generating empty statement.")
        df = pd.DataFrame(columns=['Trn Date', 'Description', 'Trn Reference', 'Cash Out', 'Cash In', 'Balance'])
    else:
        df = pd.DataFrame(rows)
        
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].apply(lambda val: ILLEGAL_CHARACTERS_RE.sub('', val) if isinstance(val, str) else val)
        
    if 'Trn Date' in df.columns:
        df['Trn Date'] = pd.to_datetime(df['Trn Date'], format='%d-%b-%Y', errors='coerce')

    for col in ['Cash Out', 'Cash In', 'Balance']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Cash In' in df.columns and 'Cash Out' in df.columns:
        df['Statement Amount'] = df['Cash In'].fillna(0) - df['Cash Out'].fillna(0)

    df.to_csv(output_path, index=False, encoding='utf-8-sig', float_format='%.2f', lineterminator='\r\n')
    
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD MMM YYYY') as writer:
        df.to_excel(writer, index=False)
    
    print(f"Successfully converted FTB! Total transactions extracted: {len(df)}")
    return True
