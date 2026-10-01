"""
ABA Bank Statement to CSV/Excel Converter
Made by: Lim Dina
"""

import pdfplumber
import pandas as pd
import sys
import argparse
import re

from banks.aba import extract_aba_statement
from banks.bred import extract_bred_statement
from banks.acleda import extract_acleda_statement
from banks.ftb import extract_ftb_statement
from banks.canadia import extract_canadia_statement

def extract_bank_statement(pdf_path, output_path, progress_callback=None, include_summary=False, bank="Auto-Detect"):
    if bank == "Auto-Detect":
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    if "Advanced Bank of Asia" in first_page_text:
                        bank = "ABA"
                    elif "Txn Date Value Date Transaction Description Debit Credit Balance" in first_page_text:
                        bank = "BRED"
                    elif "ACLEDA BANK PLC" in first_page_text or "A CLEDA BANK PLC" in first_page_text or "CASH OUT (Dr) CASH IN (Cr)" in first_page_text:
                        bank = "ACLEDA"
                    elif "OVERDRAFT ACCOUNT STATEMENT" in first_page_text or "Trn Date Description Trn Reference Cash Out Cash in Balance" in first_page_text:
                        bank = "FTB"
                    elif "Date Trans. Ref Description Credit Debit Balance" in first_page_text or "Canadia Bank Plc" in first_page_text or "contact@canadiabank.com.kh" in first_page_text:
                        bank = "CANADIA"
                    else:
                        bank = "ABA" # Default fallback
            else:
                bank = "ABA"
    
    if bank == "ABA":
        return extract_aba_statement(pdf_path, output_path, progress_callback, include_summary)
    elif bank == "BRED":
        return extract_bred_statement(pdf_path, output_path, progress_callback, include_summary)
    elif bank == "ACLEDA":
        return extract_acleda_statement(pdf_path, output_path, progress_callback, include_summary)
    elif bank == "FTB":
        return extract_ftb_statement(pdf_path, output_path, progress_callback, include_summary)
    elif bank == "CANADIA":
        return extract_canadia_statement(pdf_path, output_path, progress_callback, include_summary)
    else:
        print(f"Bank logic for {bank} is not yet implemented.")
        return False

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
