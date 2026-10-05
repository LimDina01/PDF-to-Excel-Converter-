import pdfplumber

def get_dynamic_boundaries(pdf_path):
    boundaries = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            words.sort(key=lambda w: (w['top'], w['x0']))
            
            lines = []
            current_line = []
            if not words: continue
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
                lines.append(current_line)
                
            for line in lines:
                line_text = " ".join([w['text'] for w in line])
                if 'Description' in line_text and 'Reference' in line_text and 'Balance' in line_text:
                    desc_word = next((w for w in line if 'Description'.lower() in w['text'].lower()), None)
                    ref_word = next((w for w in line if 'Reference'.lower() in w['text'].lower()), None)
                    out_word = next((w for w in line if 'Out'.lower() in w['text'].lower()), None)
                    in_word = next((w for w in line if 'In'.lower() == w['text'].lower()), None)
                    
                    if ref_word and out_word:
                        boundaries['desc_end'] = (desc_word['x1'] + ref_word['x0']) / 2 if desc_word else ref_word['x0'] - 20
                        boundaries['ref_end'] = (ref_word['x1'] + out_word['x0']) / 2
                    if out_word and in_word:
                        boundaries['out_end'] = (out_word['x1'] + in_word['x0']) / 2
                    if in_word:
                        balance_word = next((w for w in line if 'Balance'.lower() in w['text'].lower()), None)
                        if balance_word:
                            boundaries['in_end'] = (in_word['x1'] + balance_word['x0']) / 2
                    
                    print(f"Calculated boundaries for {pdf_path}: {boundaries}")
                    return boundaries

print("--- FTB Overdraft ---")
get_dynamic_boundaries(r"d:\Programming\web-converter\Test\FTB Overdraft.pdf")

print("\n--- FTB 912 ---")
get_dynamic_boundaries(r"d:\Programming\web-converter\Test\FTB 912.pdf")

