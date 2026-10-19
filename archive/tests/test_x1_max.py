import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages[:3]:
        words = page.extract_words()
        for w in words:
            # We want to find the words in the details column
            # that are not amounts. Usually amounts end with USD or are right-aligned.
            # Let's print any word that has x1 > 280 but is NOT part of an amount
            # Amounts usually have digits and commas/dots.
            if w['x1'] > 280 and w['x1'] < 330:
                print(f"Page {page.page_number}: '{w['text']}' -> x0: {w['x0']:.1f}, x1: {w['x1']:.1f}")
