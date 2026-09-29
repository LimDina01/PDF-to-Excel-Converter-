# ABA Bank Statement to CSV/Excel Converter
**Made by Lim Dina**

This tool extracts transaction data from ABA Bank Statement PDFs and converts them into a clean, uniform CSV/Excel format.

## How to use the App:
You don't need Python installed to use the app. Just double-click the `.exe` file to open the Graphical User Interface (GUI).
1. Click **Browse PDF** and select your bank statement.
2. Click **Convert to Excel / CSV** and select where you want to save the output.
3. Wait a few seconds for the success message!

---

## How to Edit and Update the Code (For Developers):
If you want to adjust the extraction logic (e.g., if a number gets too wide or you want to add support for a different bank), it is very easy to update the application!

### 1. Edit the Logic
Open `convert_statement.py` in your code editor. 
Around **Line 82**, you will find the `x` coordinates (the invisible vertical fences) that tell the scanner which column to put the text in:
```python
if x < 70:
    current_row['VALUE DATE'] += text + ' '
elif x < 160:
    current_row['TRANSACTION TYPE'] += text + ' '
elif x < 385:
    current_row['TRANSACTION DETAILS'] += text + ' '
# ... edit these numbers to shift the columns ...
```
Save the file once you are done making changes. (You do **not** need to touch `gui.py`!)

### 2. Test your changes (Optional)
To test if your new logic works before building the `.exe`, open your terminal, activate your virtual environment, and run the script:
```powershell
.\venv\Scripts\activate
python convert_statement.py
```

### 3. Re-compile the `.exe` (Update the App)
Once you are happy with the changes, you must package it back into the standalone `.exe` file so other users can run it without Python.
Run this command in your terminal:
```powershell
.\venv\Scripts\activate
pyinstaller --clean --onefile --windowed --name "ABA_GUI_App" gui.py
```

*(Note: If you are using Python 3.14 alpha and get a `base_library.zip` error, simply create an empty folder named `build/ABA_GUI_App/` before running the command!)*

Once the compiler finishes, your brand new updated `.exe` will be sitting inside the `dist/` folder! Just drag it out into your main folder, delete `build/` and `dist/`, and you are done!
