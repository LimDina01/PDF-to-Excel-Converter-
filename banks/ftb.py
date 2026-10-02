import pdfplumber
import pandas as pd
import re

def extract_ftb_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading FTB PDF: {pdf_path}")
    
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
                
                if 'Page ' in line_text or 'OVERDRAFT ACCOUNT STATEMENT' in line_text or 'From Date' in line_text or 'Printed On' in line_text or 'User :' in line_text or 'Account Detail' in line_text or 'Customer ID' in line_text or 'Customer Name' in line_text or 'Current Account Number' in line_text or 'Overdraft Loan ID' in line_text or 'Currency ' in line_text or 'Address ' in line_text or 'Account Activities' in line_text or 'Trn Date Description' in line_text or 'Detailed Account Credit' in line_text or 'Charge Debit Detailed Account' in line_text or ('Credit' in line_text and len(line) == 1) or 'This statement is computer generated' in line_text or 'not require signature' in line_text or 'Building No.' in line_text or 'Vong, Khan' in line_text or 'of receipt, other wise' in line_text or 'Email :customercare' in line_text or 'Website: www.ftb.com.kh' in line_text:
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
                            x = w['x0']
                            text = w['text']
                            if x < 420:
                                current_row['Description'] += text + ' '
                            elif x < 560:
                                current_row['Cash Out'] += text + ' '
                            elif x < 680:
                                current_row['Cash In'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '
                    else:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            if x < 80:
                                current_row['Trn Date'] += text + ' '
                            elif x < 240:
                                current_row['Description'] += text + ' '
                            elif x < 420:
                                current_row['Trn Reference'] += text + ' '
                            elif x < 560:
                                current_row['Cash Out'] += text + ' '
                            elif x < 680:
                                current_row['Cash In'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '
                else:
                    if current_row:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            if x < 240:
                                current_row['Description'] += text + ' '
                            elif x < 420:
                                current_row['Trn Reference'] += text + ' '
                            elif x < 560:
                                current_row['Cash Out'] += text + ' '
                            elif x < 680:
                                current_row['Cash In'] += text + ' '
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
        
    if 'Trn Date' in df.columns:
        df['Trn Date'] = pd.to_datetime(df['Trn Date'], format='%d-%b-%Y', errors='coerce')

    for col in ['Cash Out', 'Cash In', 'Balance']:
        if col in df.columns:
            df[col] = df[col].replace('', '0.00').replace(',', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Cash In' in df.columns and 'Cash Out' in df.columns:
        df['Statement Amount'] = df['Cash In'].fillna(0) - df['Cash Out'].fillna(0)

    df.to_csv(output_path, index=False, encoding='utf-8-sig', float_format='%.2f', lineterminator='\r\n')
    
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD MMM YYYY') as writer:
        df.to_excel(writer, index=False)
    
    print(f"Successfully converted FTB! Total transactions extracted: {len(df)}")
    return True
