"""
ABA Bank Statement to CSV/Excel Converter
Made by: Lim Dina
"""

import pdfplumber
import pandas as pd
import sys
import argparse
import re

def extract_bank_statement(pdf_path, output_path, progress_callback=None, include_summary=False):
    print(f"Reading PDF: {pdf_path}")
    
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
                    lines.append(current_line)
                    current_line = [w]
                    current_top = w['top']
                else:
                    current_line.append(w)
            
            if current_line:
                lines.append(current_line)
                
            # Process each line
            for line in lines:
                # Reconstruct the line text for regex checking
                line_text = " ".join([w['text'] for w in line])
                
                # Check if this line is a footer or disclaimer to skip
                if 'Generated on:' in line_text or 'DISCLAIMER:' in line_text or 'Page ' in line_text or 'Advanced Bank of Asia' in line_text or 'ACCOUNT STATEMENT' in line_text:
                    continue
                    
                # Skip table headers so they don't get accidentally glued to the previous row
                if 'TRANSACTION TYPE' in line_text and 'TRANSACTION DETAILS' in line_text:
                    seen_table_headers = True
                    continue
                
                # Check if it's the start of a new transaction (starts with Date: DD Mmm YYYY)
                # First two words should be 'DD' and 'Mmm'
                is_new_row = False
                if len(line) >= 3:
                    date_str = f"{line[0]['text']} {line[1]['text']} {line[2]['text']}"
                    if re.match(r'^\d{2} [A-Z][a-z]{2} \d{4}$', date_str):
                        is_new_row = True
                        has_started_transactions = True
                
                is_summary_row = False
                if include_summary:
                    if line_text.startswith("Opening Balance") and "Total" not in line_text and seen_table_headers:
                        is_summary_row = True
                    elif has_started_transactions:
                        if line_text.startswith("Closing Balance") or line_text.startswith("Total Blocked Amounts") or line_text.startswith("Blocked Amounts"):
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
                        # Assign words to columns based on x0 coordinate
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            
                            if x < 70:
                                current_row['VALUE DATE'] += text + ' '
                            elif x < 160:
                                current_row['TRANSACTION TYPE'] += text + ' '
                            elif x < 385:
                                current_row['TRANSACTION DETAILS'] += text + ' '
                            elif x < 455:
                                current_row['MONEY IN'] += text + ' '
                            elif x < 550:
                                current_row['MONEY OUT'] += text + ' '
                            else:
                                current_row['BALANCE'] += text + ' '
                else:
                    # It's a continuation line. 
                    # Usually, this is just TRANSACTION DETAILS continuing.
                    if current_row:
                        for w in line:
                            x = w['x0']
                            text = w['text']
                            
                            # Append to details if it's in the details or type area
                            if 70 <= x < 385:
                                current_row['TRANSACTION DETAILS'] += text + ' '
                            
    # Append the last row
    if current_row:
        rows.append(current_row)
    
    if not rows:
        print("No transactions found in the PDF. Please check the PDF format.")
        return False

    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    # Clean up trailing spaces
    for col in df.columns:
        df[col] = df[col].str.strip()
        
    # Convert 'VALUE DATE' to actual datetime objects so Excel recognizes them as dates
    if 'VALUE DATE' in df.columns:
        df['VALUE DATE'] = pd.to_datetime(df['VALUE DATE'], format='%d %b %Y', errors='coerce')

    # Clean up currency columns (remove commas, handle empty strings)
    for col in ['MONEY IN', 'MONEY OUT', 'BALANCE']:
        if col in df.columns:
            df[col] = df[col].replace('', '0.00').replace(',', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add 'Statement Amount' column (Money In - Money Out)
    if 'MONEY IN' in df.columns and 'MONEY OUT' in df.columns:
        money_in = df['MONEY IN'].fillna(0)
        money_out = df['MONEY OUT'].fillna(0)
        df['Statement Amount'] = money_in - money_out

    # Save to CSV
    print(f"Exporting data to: {output_path}")
    df.to_csv(output_path, index=False)
    
    # Also save to Excel for convenience
    excel_path = output_path.replace('.csv', '.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl', datetime_format='DD MMM YYYY') as writer:
        df.to_excel(writer, index=False)
    print(f"Also exported to Excel: {excel_path}")
    
    print(f"Successfully converted! Total transactions extracted: {len(df)}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User dragged and dropped a file, or used command line
        parser = argparse.ArgumentParser(description="Convert ABA Bank Statement PDF to CSV")
        parser.add_argument("input_pdf", help="Path to the input PDF file")
        parser.add_argument("--output", "-o", default="statement_output.csv", help="Path to the output CSV file")
        args = parser.parse_args()
        input_pdf = args.input_pdf
        output = args.output
    else:
        # User just double-clicked the .exe
        print("========================================================")
        print("       ABA Bank Statement to CSV/Excel Converter        ")
        print("========================================================")
        
        # Open a standard Windows file picker dialog
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw() # Hide the main empty window
            root.attributes('-topmost', True) # Bring dialog to front
            
            print("\nPlease select your PDF file from the window that just popped up...")
            input_pdf = filedialog.askopenfilename(
                title="Select ABA Bank Statement PDF",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            root.destroy()
            
            if not input_pdf:
                print("No input file was selected. Cancelling...")
                output = None
            else:
                import os
                default_name = os.path.splitext(os.path.basename(input_pdf))[0] + "_converted.csv"
                print("Please choose where you want to save the converted file...")
                output = filedialog.asksaveasfilename(
                    title="Save converted file as...",
                    initialfile=default_name,
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")]
                )
                if not output:
                    print("No save location selected. Cancelling...")
                    input_pdf = None
            
        except ImportError:
            print("\nYou didn't provide a PDF file.")
            input_pdf = input("Please type or paste the path to your PDF file here: ").strip('"').strip("'").strip()
            output = "output_for_bc.csv"
        
    if input_pdf:
        try:
            success = extract_bank_statement(input_pdf, output)
            if success:
                import os
                import subprocess
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    if messagebox.askyesno("Success", f"Conversion successful!\n\nDo you want to open the destination folder?"):
                        filepath = os.path.normpath(os.path.abspath(output))
                        subprocess.Popen(f'explorer /select,"{filepath}"')
                    root.destroy()
                except ImportError:
                    pass
        except Exception as e:
            print(f"An error occurred: {e}")
        
    print("\nPress Enter to exit...")
    input()
