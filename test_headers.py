import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    
    for w in words:
        if 'Money' in w['text'] or 'In' in w['text'] or 'Out' in w['text'] or 'Balance' in w['text']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
