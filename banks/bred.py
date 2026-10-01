import pdfplumber
import pandas as pd
import re

def extract_bred_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading BRED PDF: {pdf_path}")
    
    rows = []
    current_row = None
    
    # Open the PDF
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            if progress_callback:
                progress_callback(i + 1, total_pages)
            print(f"Extracting page {i + 1}...")
            
            words = page.extract_words()
            if not words:
                continue
                
            # Group words into lines
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
                
                # Skip headers and footers
                if 'Page ' in line_text or 'Txn Date' in line_text or 'End of Statement' in line_text or 'No. 30, Preah' in line_text or 'Statement Period' in line_text or 'Name :' in line_text or 'Address :' in line_text or 'Customer No.' in line_text or 'Account No.' in line_text or 'Account Currency' in line_text or 'Account Title' in line_text or 'Account Type' in line_text or 'Start Date' in line_text or 'End Date' in line_text:
                    continue
                    
                is_summary_row = False
                if include_summary:
                    if 'Opening Balance :' in line_text or 'Closing Balance :' in line_text:
                        is_summary_row = True
                        
                is_new_row = False
                if len(line) >= 2:
                    date_str = line[0]['text']
                    if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
                        is_new_row = True
                        
                if is_new_row or is_summary_row:
                    if current_row:
                        rows.append(current_row)
                        
                    current_row = {
                        'Txn Date': '',
                        'Value Date': '',
                        'Transaction Description': '',
                        'Debit': '',
                        'Credit': '',
                        'Balance': ''
                    }
                    
                    if is_summary_row:
                        current_row['Transaction Description'] = line_text
                    else:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            
                            if x < 85:
                                current_row['Txn Date'] += text + ' '
                            elif x < 130:
                                current_row['Value Date'] += text + ' '
                            elif x < 340:
                                current_row['Transaction Description'] += text + ' '
                            elif x < 420:
                                current_row['Debit'] += text + ' '
                            elif x < 510:
                                current_row['Credit'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '
                else:
                    if current_row and not is_summary_row:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            
                            if x < 340:
                                current_row['Transaction Description'] += text + ' '
                            elif x < 420:
                                current_row['Debit'] += text + ' '
                            elif x < 510:
                                current_row['Credit'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '

    if current_row:
        rows.append(current_row)
    
    if not rows:
        print("No transactions found in the PDF.")
        return False

    df = pd.DataFrame(rows)
    for col in df.columns:
        df[col] = df[col].str.strip()
        
    for date_col in ['Txn Date', 'Value Date']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format='%d-%m-%Y', errors='coerce')

    for col in ['Debit', 'Credit', 'Balance']:
        if col in df.columns:
            df[col] = df[col].replace('', '0.00').replace(',', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Credit' in df.columns and 'Debit' in df.columns:
        df['Statement Amount'] = df['Credit'].fillna(0) - df['Debit'].fillna(0)

    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD-MM-YYYY') as writer:
        df.to_excel(writer, index=False)
    
    print(f"Successfully converted BRED! Total transactions extracted: {len(df)}")
    return True
