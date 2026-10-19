import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\FTB Overdraft.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    
    print("--- Transactions ---")
    for w in words:
        if '3,000,000.00' in w['text'] or 'FT26250RL1DP' in w['text']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
