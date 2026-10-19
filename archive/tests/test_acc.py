import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[1]
    words = page.extract_words()
    words.sort(key=lambda w: (w['top'], w['x0']))
    
    for w in words:
        if 'ACTIVITY' in w['text'] or 'ACCOUNT' in w['text']:
            print(f"'{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
