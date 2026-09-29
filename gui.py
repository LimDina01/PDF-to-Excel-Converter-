import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from convert_statement import extract_bank_statement
import os

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ABA Bank Statement Converter")
        self.root.geometry("500x250")
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
        title.pack(pady=(0, 20))
        
        # File Selection Frame
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = ttk.Label(file_frame, text="No file selected...", foreground="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_browse = ttk.Button(file_frame, text="Browse PDF", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)
        
        # Status Label
        self.status_label = ttk.Label(frame, text="", foreground="blue")
        self.status_label.pack(pady=10)
        
        # Convert Button
        self.btn_convert = ttk.Button(frame, text="Convert to Excel / CSV", command=self.convert_file, state=tk.DISABLED)
        self.btn_convert.pack(fill=tk.X, pady=10, ipady=5)
        
        # Footer
        footer = ttk.Label(frame, text="Made by Lim Dina", font=("Segoe UI", 8), foreground="gray")
        footer.pack(side=tk.BOTTOM)

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
        self.root.update()
        
        # Run conversion in a separate thread so UI doesn't freeze
        threading.Thread(target=self.run_conversion, args=(self.pdf_path, output_path), daemon=True).start()
        
    def run_conversion(self, input_path, output_path):
        try:
            # We call the exact same logic we built earlier!
            extract_bank_statement(input_path, output_path)
            self.root.after(0, self.conversion_success)
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))
            
    def conversion_success(self):
        self.status_label.config(text="Done! Successfully converted.", foreground="green")
        messagebox.showinfo("Success", "Your bank statement has been converted successfully!")
        self.btn_convert.config(state=tk.NORMAL)
        
    def conversion_error(self, error_msg):
        self.status_label.config(text="An error occurred.", foreground="red")
        messagebox.showerror("Error", f"Failed to convert file:\n\n{error_msg}")
        self.btn_convert.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
