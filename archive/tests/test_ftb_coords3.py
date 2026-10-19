import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\FTB 912.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    
    print("--- FTB 912 ---")
    for w in words[:50]:
        if w['text'] in ['Trn', 'Date', 'Description', 'Reference', 'Cash', 'Out', 'In', 'Balance'] or '-' in w['text']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
