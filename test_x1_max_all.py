import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        words = page.extract_words()
        for w in words:
            # Check for words from transaction details that go past x1=280
            # Exclude disclaimers, headers, and amounts
            text = w['text']
            if w['x1'] > 280 and w['x1'] < 330:
                if 'DigitalSupport' not in text and 'ababank' not in text and 'damage' not in text and 'loss' not in text and 'Upon' not in text and 'code' not in text and 'QR' not in text and 'for' not in text and 'a' != text and 'any' != text and '.' != text:
                    print(f"Page {page.page_number}: '{text}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
