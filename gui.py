import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from convert_statement import extract_bank_statement
import os

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Bank Statement Converter")
        
        window_width = 500
        window_height = 310
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)
        
        # Use native Windows styling
        self.style = ttk.Style()
        try:
            self.style.theme_use('vista')
        except:
            pass # Fallback to default if not available
            
        self.pdf_path = None
        
        # Main Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title Label
        title = ttk.Label(frame, text="Bank Statement to CSV/Excel", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 5))
        
        # Disclaimer under title
        disclaimer = ttk.Label(frame, text="⚠️ Disclaimer: Converted data may not be 100% accurate. Please review before use.", font=("Segoe UI", 8), foreground="red")
        disclaimer.pack(pady=(0, 15))
        
        # File Selection Frame
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = ttk.Label(file_frame, text="No file selected...", foreground="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_browse = ttk.Button(file_frame, text="Browse PDF", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)
        
        # Bank Selection Frame
        bank_frame = ttk.Frame(frame)
        bank_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(bank_frame, text="Select Bank Format:").pack(side=tk.LEFT)
        
        self.bank_var = tk.StringVar(value="Auto-Detect")
        banks = ["Auto-Detect", "ABA", "CANADIA", "FTB", "BRED", "ACLEDA"]
        self.bank_dropdown = ttk.Combobox(bank_frame, textvariable=self.bank_var, values=banks, state="readonly", width=15)
        self.bank_dropdown.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status Label
        self.status_label = ttk.Label(frame, text="", foreground="blue")
        self.status_label.pack(pady=(10, 5))
        
        # Progress Bar (hidden initially)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        
        # Checkbox for Summary Rows
        self.include_summary_var = tk.BooleanVar(value=False)
        self.chk_summary = ttk.Checkbutton(frame, text="Include Opening/Closing Balances and Summary Details", variable=self.include_summary_var)
        self.chk_summary.pack(pady=(5, 0))

        # Convert Button
        self.btn_convert = ttk.Button(frame, text="Convert to Excel / CSV", command=self.convert_file, state=tk.DISABLED)
        self.btn_convert.pack(fill=tk.X, pady=10, ipady=5)
        
        # Footer Frame
        footer_frame = ttk.Frame(frame)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        lbl_company = ttk.Label(footer_frame, text="CBVH", font=("Segoe UI", 8, "bold"), foreground="gray")
        lbl_company.pack(side=tk.LEFT)
        
        lbl_author = ttk.Label(footer_frame, text="Made by Lim Dina", font=("Segoe UI", 8), foreground="gray")
        lbl_author.pack(side=tk.RIGHT)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select ABA Bank Statement PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.pdf_path = filename
            self.file_label.config(text=os.path.basename(filename), foreground="black")
            self.btn_convert.config(state=tk.NORMAL)
            self.status_label.config(text="Ready to convert.")

    def convert_file(self):
        if not self.pdf_path:
            return
            
        default_name = os.path.splitext(os.path.basename(self.pdf_path))[0] + "_converted.csv"
        output_path = filedialog.asksaveasfilename(
            title="Save converted file as...",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if not output_path:
            return
            
        self.btn_convert.config(state=tk.DISABLED)
        self.status_label.config(text="Converting... Please wait (this may take a few seconds).")
        self.progress_var.set(0)
        self.progress.pack(fill=tk.X, pady=(0, 10))
        self.root.update()
        
        # Run conversion in a separate thread so UI doesn't freeze
        selected_bank = self.bank_var.get()
        threading.Thread(target=self.run_conversion, args=(self.pdf_path, output_path, selected_bank), daemon=True).start()
        
    def run_conversion(self, input_path, output_path, selected_bank):
        try:
            def update_progress(current, total):
                percent = (current / total) * 100
                self.root.after(0, self.progress_var.set, percent)
                self.root.after(0, self.status_label.config, {'text': f"Extracting page {current} of {total}..."})

            # We call the exact same logic we built earlier!
            include_summary = self.include_summary_var.get()
            success = extract_bank_statement(input_path, output_path, progress_callback=update_progress, include_summary=include_summary, bank=selected_bank)
            
            if success:
                self.root.after(0, lambda: self.conversion_success(output_path))
            else:
                self.root.after(0, lambda: self.conversion_error("No transactions found or extraction failed."))
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))
        finally:
            self.root.after(0, self.progress.pack_forget)
            
    def conversion_success(self, output_path):
        self.status_label.config(text="Done! Successfully converted.", foreground="green")
        if messagebox.askyesno("Success", "Your bank statement has been converted successfully!\n\nDo you want to open the destination folder?"):
            import subprocess
            filepath = os.path.normpath(os.path.abspath(output_path))
            subprocess.Popen(f'explorer /select,"{filepath}"')
        self.btn_convert.config(state=tk.NORMAL)
        
    def conversion_error(self, error_msg):
        self.status_label.config(text="An error occurred.", foreground="red")
        messagebox.showerror("Error", f"Failed to convert file:\n\n{error_msg}")
        self.btn_convert.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
