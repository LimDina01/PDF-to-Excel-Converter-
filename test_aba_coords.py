import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 262.pdf"

print(f"Reading {pdf_path}")
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0] # Just the first page
    words = page.extract_words()
    
    words.sort(key=lambda w: (w['top'], w['x0']))
    
    lines = []
    current_line = []
    if words:
        current_top = words[0]['top']
        for w in words:
            if abs(w['top'] - current_top) > 3:
                current_line.sort(key=lambda x: x['x0'])
                lines.append(current_line)
                current_line = [w]
                current_top = w['top']
            else:
                current_line.append(w)
        if current_line:
            current_line.sort(key=lambda x: x['x0'])
            lines.append(current_line)

    for i, line in enumerate(lines[:35]):
        if any('12,030.71' in w['text'] for w in line) or any('20,000.00' in w['text'] for w in line):
            print(f"Line {i}: {' '.join([w['text'] for w in line])}")
            for w in line:
                print(f"  -> '{w['text']}' at x0: {w['x0']:.1f}, top: {w['top']:.1f}")
