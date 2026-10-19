import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\FTB 912.pdf"
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
        if '03-Sep-2026' in w['text'] or 'FT26246LWYVR/BTK' in w['text'] or '63,886,300.00' in w['text'] or '64,296,466.66' in w['text']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
