import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\FTB Overdraft.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    words.sort(key=lambda w: (w['top'], w['x0']))
    
    print("--- Headers ---")
    for w in words:
        if w['text'] in ['Trn', 'Date', 'Description', 'Reference', 'Cash', 'Out', 'In', 'Balance']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
            
    print("\n--- Transactions ---")
    for w in words:
        if 'FT26245B1L2F' in w['text'] or '500,000.00' in w['text'] or '-2,893,896.56' in w['text'] or 'CHECK' in w['text']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
