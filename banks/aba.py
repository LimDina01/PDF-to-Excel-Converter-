import pdfplumber
import pandas as pd
import re
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

def extract_aba_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading ABA PDF: {pdf_path}")
    
    rows = []
    current_row = None
    has_started_transactions = False
    seen_table_headers = False
    
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
                
            # Group words into lines based on vertical position (top)
            # A tolerance of 3 points is usually safe for the same line
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
                
            # Process each line
            for line in lines:
                # Reconstruct the line text for regex checking
                line_text = " ".join([w['text'] for w in line])
                
                # Check if this line is a footer, watermark, or disclaimer to skip
                if any(skip_word in line_text for skip_word in [
                    'Generated on:', 'DISCLAIMER:', 'Page ', 'Advanced Bank of Asia', 
                    'ACCOUNT STATEMENT', 'ACCOUNT ACTIVITY', 'reliance', 'document is free', 
                    'The authenticity verification', 'verify.ababank.com', 'contact ABA Bank directly'
                ]):
                    continue
                    
                # Skip table headers so they don't get accidentally glued to the previous row
                if 'TRANSACTION TYPE' in line_text or ('Date' in line_text and 'Transaction Details' in line_text):
                    seen_table_headers = True
                    continue
                
                # Check if it's the start of a new transaction (starts with Date)
                is_new_row = False
                if len(line) >= 3:
                    # The date must actually be in the Date column (x0 < 90) to be a new row!
                    if line[0]['x0'] < 90:
                        date_str = f"{line[0]['text']} {line[1]['text']} {line[2]['text']}"
                        # Match old format "01 Sep 2026" or new format "Sep 01, 2026"
                        if re.match(r'^\d{2} [A-Z][a-z]{2} \d{4}$', date_str) or re.match(r'^[A-Z][a-z]{2} \d{2}, \d{4}$', date_str):
                            is_new_row = True
                            has_started_transactions = True
                
                is_summary_row = False
                if include_summary:
                    if line_text.startswith("Opening Balance") and "Total" not in line_text and seen_table_headers:
                        is_summary_row = True
                    elif has_started_transactions:
                        if line_text.startswith("Closing Balance") or line_text.startswith("Ending Balance") or line_text.startswith("Total Money In") or line_text.startswith("Total Money Out") or line_text.startswith("Credit Balance") or line_text.startswith("Total Blocked Amounts") or line_text.startswith("Blocked Amounts"):
                            is_summary_row = True
                        elif line_text.startswith("Balance ") or line_text == "Balance":
                            is_summary_row = True
                
                if is_new_row or is_summary_row:
                    if current_row:
                        rows.append(current_row)
                        
                    current_row = {
                        'VALUE DATE': '',
                        'TRANSACTION DETAILS': '',
                        'MONEY IN': '',
                        'MONEY OUT': '',
                        'BALANCE': ''
                    }
                    
                    if is_summary_row:
                        if line_text.startswith("Blocked Amounts") and not line_text.startswith("Total"):
                            current_row['TRANSACTION DETAILS'] = "Blocked Amounts"
                        else:
                            # For summary rows, place the text in DETAILS and the number in BALANCE
                            for w in line:
                                x = w['x0']
                                text = w['text']
                                # Typical balance numbers are on the far right
                                if x > 400 and bool(re.search(r'\d', text)):
                                    current_row['BALANCE'] += text + ' '
                                else:
                                    current_row['TRANSACTION DETAILS'] += text + ' '
                    else:
                        # Assign words to columns based on x1 coordinate for amounts, x0 for date
                        for w in line:
                            x0 = w['x0']
                            x1 = w['x1']
                            text = w['text']
                            
                            if x0 < 90:
                                current_row['VALUE DATE'] += text + ' '
                            elif x1 < 290:
                                current_row['TRANSACTION DETAILS'] += text + ' '
                            elif x1 < 390:
                                current_row['MONEY IN'] += text + ' '
                            elif x1 < 480:
                                current_row['MONEY OUT'] += text + ' '
                            else:
                                current_row['BALANCE'] += text + ' '
                else:
                    # It's a continuation line. 
                    if current_row:
                        for w in line:
                            x0 = w['x0']
                            x1 = w['x1']
                            text = w['text']
                            
                            if x0 < 90:
                                current_row['VALUE DATE'] += text + ' '
                            elif x1 < 290:
                                current_row['TRANSACTION DETAILS'] += text + ' '
                            elif x1 < 390:
                                current_row['MONEY IN'] += text + ' '
                            elif x1 < 480:
                                current_row['MONEY OUT'] += text + ' '
                            else:
                                current_row['BALANCE'] += text + ' '
                            
    # Append the last row
    if current_row:
        rows.append(current_row)
    
    if not rows:
        print("No transactions found in the PDF. Generating empty statement.")
        df = pd.DataFrame(columns=['VALUE DATE', 'TRANSACTION DETAILS', 'MONEY IN', 'MONEY OUT', 'BALANCE'])
    else:
        # Convert to DataFrame
        df = pd.DataFrame(rows)
    
    # Clean up trailing spaces
    for col in df.columns:
        df[col] = df[col].str.strip()
        
    # Convert 'VALUE DATE' to actual datetime objects so Excel recognizes them as dates
    if 'VALUE DATE' in df.columns:
        df['VALUE DATE'] = pd.to_datetime(df['VALUE DATE'], errors='coerce')

    # Clean up currency columns (remove commas, USD, KHR, handle empty strings)
    for col in ['MONEY IN', 'MONEY OUT', 'BALANCE']:
        if col in df.columns:
            # Keep only digits, minus signs, and decimal points
            df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
            df[col] = df[col].replace('', '0.00')
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add 'Statement Amount' column (Money In - Money Out)
    if 'MONEY IN' in df.columns and 'MONEY OUT' in df.columns:
        money_in = df['MONEY IN'].fillna(0)
        money_out = df['MONEY OUT'].fillna(0)
        df['Statement Amount'] = money_in - money_out

    # Strip illegal characters that crash Excel (openpyxl)
    def clean_illegal_chars(val):
        if not isinstance(val, str):
            return val
        return ILLEGAL_CHARACTERS_RE.sub('', val)

    for col in df.columns:
        df[col] = df[col].apply(clean_illegal_chars)

    # Save to CSV
    print(f"Exporting data to: {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8-sig', float_format='%.2f', lineterminator='\r\n')
    
    # Also save to Excel for convenience
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD MMM YYYY') as writer:
        df.to_excel(writer, index=False)
    print(f"Also exported to Excel: {excel_path}")
    
    print(f"Successfully converted ABA! Total transactions extracted: {len(df)}")
    return True
