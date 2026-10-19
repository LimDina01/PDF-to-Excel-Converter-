import os
import django
import pandas as pd
import pdfplumber
import re

pdf_path = r'd:\Programming\web-converter\Test\ABA 262.pdf'

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages[:2]:
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
                
        for line in lines:
            line_text = " ".join([w['text'] for w in line])
            if 'NAO NATENG' in line_text or 'QR Code' in line_text:
                print(f"--- Line: {line_text} ---")
                for w in line:
                    x1 = w['x1']
                    if x1 < 290: col = 'DETAILS'
                    elif x1 < 390: col = 'MONEY IN'
                    elif x1 < 480: col = 'MONEY OUT'
                    else: col = 'BALANCE'
                    print(f"'{w['text']}' -> {col} (x1={x1:.1f})")
