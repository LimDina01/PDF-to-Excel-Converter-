import pdfplumber

pdf_path = r"d:\Programming\web-converter\Test\ACL 517.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages[:2]:
        print(f"--- PAGE {page.page_number} ---")
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
                
        for i, line in enumerate(lines[:30]):
            line_text = " ".join([w['text'] for w in line])
            print(f"Line {i}: {line_text}")
