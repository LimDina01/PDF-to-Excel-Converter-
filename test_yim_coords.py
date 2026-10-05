import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[1] # Page 2, where YIM NARETH is
    words = page.extract_words()
    words.sort(key=lambda w: (w['top'], w['x0']))
    
    for w in words:
        if '1,050.00' in w['text']:
            print(f"'{w['text']}' at x0: {w['x0']:.1f}, x1: {w['x1']:.1f}, top: {w['top']:.1f}")
