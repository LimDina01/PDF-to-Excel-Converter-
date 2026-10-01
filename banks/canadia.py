import pdfplumber
import pandas as pd
import re

def extract_canadia_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading CANADIA PDF: {pdf_path}")
    
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
                
                if 'ACCOUNT STATEMENT' in line_text or 'Statement Period:' in line_text or 'Generated Date:' in line_text or 'DETAILS SUMMARY' in line_text or 'Account Holder:' in line_text or 'Customer ID:' in line_text or 'Account Number:' in line_text or 'Account Type:' in line_text or 'Account Currency:' in line_text or 'Date Trans. Ref Description Credit Debit Balance' in line_text or 'Disclaimer:' in line_text or 'ensuring the accuracy of all information' in line_text or 'amounts, and beneficiary details' in line_text or 'Canadia Bank Plc.' in line_text or 'Email: contact@canadiabank.com.kh' in line_text or 'LAK2, Phum11, Tuek' in line_text or 'Kouk, Phnom Penh, Cambodia' in line_text or 'NO.286;ST.146;PHUM11;SK.TUEK' in line_text:
                    continue
                    
                is_summary_row = False
                if include_summary:
                    if 'Beginning Balance:' in line_text or 'Ending Balance:' in line_text or 'Total Debit:' in line_text or 'Total Credit:' in line_text:
                        is_summary_row = True
                        
                is_new_row = False
                if len(line) >= 3:
                    date_str = f"{line[0]['text']} {line[1]['text']} {line[2]['text']}"
                    if re.match(r'^\d{2} [A-Z][a-z]{2} \d{4}$', date_str):
                        is_new_row = True
                        
                if is_new_row or is_summary_row:
                    if current_row:
                        rows.append(current_row)
                        
                    current_row = {
                        'Date': '',
                        'Trans. Ref': '',
                        'Description': '',
                        'Credit': '',
                        'Debit': '',
                        'Balance': ''
                    }
                    
                    if is_summary_row:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            if x < 420:
                                current_row['Description'] += text + ' '
                            elif x < 470:
                                current_row['Credit'] += text + ' '
                            elif x < 520:
                                current_row['Debit'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '
                    else:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            if x < 80:
                                current_row['Date'] += text + ' '
                            elif x < 230:
                                current_row['Trans. Ref'] += text + ' '
                            elif x < 420:
                                current_row['Description'] += text + ' '
                            elif x < 470:
                                current_row['Credit'] += text + ' '
                            elif x < 520:
                                current_row['Debit'] += text + ' '
                            else:
                                current_row['Balance'] += text + ' '
                else:
                    if current_row:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            if x < 80:
                                current_row['Date'] += text + ' '
                            elif x < 230:
                                current_row['Trans. Ref'] += text + ' '
                            elif x < 420:
                                current_row['Description'] += text + ' '
                            elif x < 470:
                                current_row['Credit'] += text + ' '
                            elif x < 520:
                                current_row['Debit'] += text + ' '
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
        
    if 'Date' in df.columns:
        df['Date'] = df['Date'].str.replace(r' \d{2}:\d{2} (AM|PM)', '', regex=True)
        df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y', errors='coerce')

    if 'Trans. Ref' in df.columns:
        # Force Excel to treat the long numerical string as text instead of scientific notation
        df['Trans. Ref'] = df['Trans. Ref'].apply(lambda x: f'="{x}"' if pd.notnull(x) and x != '' else x)

    for col in ['Credit', 'Debit', 'Balance']:
        if col in df.columns:
            df[col] = df[col].replace('USD', '', regex=True).replace('', '0.00').replace(',', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Credit' in df.columns and 'Debit' in df.columns:
        df['Statement Amount'] = df['Credit'].fillna(0) - df['Debit'].fillna(0)

    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD MMM YYYY') as writer:
        df.to_excel(writer, index=False)
    
    print(f"Successfully converted CANADIA! Total transactions extracted: {len(df)}")
    return True
