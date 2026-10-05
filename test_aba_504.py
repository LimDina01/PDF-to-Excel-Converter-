import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ABA 504.pdf"

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

    for i, line in enumerate(lines[:35]): # Print first 35 lines
        line_text = " ".join([w['text'] for w in line])
        print(f"Line {i}: {line_text}")
        if i > 15: # print details of a few lines
            for w in line:
                print(f"  -> '{w['text']}' at x0: {w['x0']:.1f}")
