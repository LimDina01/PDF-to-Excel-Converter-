"""
Khmer Unicode Normalization & Bank Remark Cleaner
Provides cleaning and post-processing for Khmer script extracted from Cambodian bank statements
(ABA, ACLEDA, FTB, Canadia, BRED).
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Dictionary of known bank remark ligature and broken font patterns
# Matches both NUL byte (\x00) and replacement character (\ufffe) drops
# ---------------------------------------------------------------------------
KHMER_BANK_REPLACEMENTS = [
    # Customer keyword ("ភ្ញៀវ")
    (re.compile(r'េភ[\x00\ufffe\ufffd\s]*វ|ភេវ'), 'ភ្ញៀវ'),
    
    # Settlement / Installment / Payment / Ledger
    (re.compile(r'សក្ាប់\s*ររ់'), 'សម្រាប់កក់'),
    (re.compile(r'សក្ាប់'), 'សម្រាប់'),
    (re.compile(r'បញ្[ឍហ][ីឺ]'), 'បញ្ជី'),
    (re.compile(r'ទូ[\x00\ufffe\ufffd\s]*ត់'), 'ទូទាត់'),
    (re.compile(r'េលីកទី'), 'លើកទី'),
    (re.compile(r'ទិញរេទះរញុ'), 'ទិញរទេះរុញ'),
    (re.compile(r'ទឹក[\x00\ufffe\ufffd\s]*តេច[\x00\ufffe\ufffd\s]*ក[\x00\ufffe\ufffd\s]*ំ|ទឹកតេចកំ'), 'ទឹកត្រចៀកកាំ'),
    (re.compile(r'ស[\x00\ufffe\ufffd\s]*រៈផលិតកម[\x00\ufffe\ufffd\s]*|ផលិតកម[\x00\ufffe\ufffd\s]*'), 'សម្ភារៈផលិតកម្ម'),
    (re.compile(r'ជូនបង[\x00\ufffe\ufffd\s]*ប[\x00\ufffe\ufffd\s]*ែំខ'), 'ជូនបងប្រចាំខែ'),
    (re.compile(r'បងលក់េព[\x00\ufffe\ufffd\s]*ជ[\x00\ufffe\ufffd\s]*យ'), 'បង់លក់ពេជ្រ'),
    (re.compile(r'ជេណី[\x00\ufffe\ufffd\s]*រ'), 'ជណ្ដើរ'),
    
    # Common names / syllables visual fixes
    (re.compile(r'ចំេរ[\x00\ufffe\ufffd\s]*ន'), 'ចំរើន'),
    (re.compile(r'ច័ន[\x00\ufffe\ufffd\s]*និមល'), 'ច័ន្ទនិមល'),
    (re.compile(r'ច័ន[\x00\ufffe\ufffd\s]*ចរៃណ'), 'ច័ន្ទចរណៃ'),
    (re.compile(r'េគ[\x00\ufffe\ufffd\s]*វ'), 'កែវ'),
    (re.compile(r'េព[\x00\ufffe\ufffd\s]*ជ'), 'ពេជ្រ'),
    (re.compile(r'ែហម'), 'ហែម'),
    
    # ACLEDA & Addresses
    (re.compile(r'ទកឺ\s*ល្កអ\s*់'), 'ទឹកល្អក់'),
    (re.compile(r'ទួល្គ\s*កោ|ទួល្គ\s*ោក'), 'ទួលគោក'),
    (re.compile(r'ភ្ំគនេញ|ភ្នំ\s*គេញ'), 'ភ្នំពេញ'),
    (re.compile(r'ភ្ញៀវលក់ភ្រឿង'), 'ភ្ញៀវលក់គ្រឿង'),
    
    # FTB Statement Artifacts
    (re.compile(r'សɳȶង្ខេប'), 'សង្ខេប'),
    (re.compile(r'[a-zA-Z\x80-\xff]+(?=[\u1780-\u17FF]{3,})'), ''),
]

# Patterns for contextual visual-to-logical reordering of left-hanging vowels [េែៃ] (U+17C1, U+17C2, U+17C3)
P_VISUAL_VOWEL_START = re.compile(r'(?:^|(?<=[\s\(\)\[\]\-:,._/|^~]))([េែៃ])([\u1780-\u17B3](?:\u17D2[\u1780-\u17B3])*)')
P_VISUAL_VOWEL_AFTER = re.compile(r'(?<=[\u17B6-\u17D3])([េែៃ])([\u1780-\u17B3](?:\u17D2[\u1780-\u17B3])*)')


def clean_khmer_text(text: str) -> str:
    """
    Cleans, repairs font ligature drops, normalizes spacing, and restores
    standard Unicode order for Khmer text extracted from bank statement PDFs.
    
    Safe to apply to all DataFrame values (non-Khmer text and numbers remain intact).
    """
    if not isinstance(text, str):
        return text
        
    # Quickly skip strings that contain no Khmer characters or ligature markers
    has_khmer = any(0x1780 <= ord(c) <= 0x17FF for c in text)
    if not has_khmer and '\ufffe' not in text and '\x00' not in text:
        return text.strip()
        
    cleaned = text
    
    # 1. Apply known Cambodian bank remark pattern repairs (e.g. ភ្ញៀវ, ទូទាត់, etc.)
    for pattern, repl in KHMER_BANK_REPLACEMENTS:
        cleaned = pattern.sub(repl, cleaned)
        
    # 2. Recover split vowel IE (េ + Consonant + \x00 -> Consonant + ៀ)
    # Bank fonts split the ៀ vowel glyph into visual េ and right-side mark \x00
    cleaned = re.sub(r'េ([\u1780-\u17B3])[\x00\ufffe\ufffd]', lambda m: m.group(1) + '\u17C0', cleaned)
    
    # 3. Recover dropped Mo + Muusikatoan (ម + ៉) ligatures that mapped to \x00
    cleaned = re.sub(r'[\x00\ufffe\ufffd]៉(?=[\s]*[\u1780-\u17B3][\u17CB])', 'ម៉', cleaned)
    cleaned = re.sub(r'[\x00\ufffe\ufffd]៉', 'ម៉ា', cleaned)
    cleaned = re.sub(r'(ម៉ា?)\s+(?=[\u1780-\u17B3])', r'\1', cleaned)
        
    # 4. Strip leftover non-character and null markers (\x00, \ufffe, \ufffd)
    cleaned = cleaned.replace('\x00', '').replace('\ufffe', '').replace('\ufffd', '')
    
    # 5. Clean zero-width space characters inside Khmer words
    cleaned = cleaned.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    # 6. Contextual Visual-to-Logical reordering of left-hanging vowels
    cleaned = P_VISUAL_VOWEL_START.sub(r'\2\1', cleaned)
    cleaned = P_VISUAL_VOWEL_AFTER.sub(r'\2\1', cleaned)
    
    # 7. Compose split compound vowels into standard Unicode vowels
    # e.g., េ + ា -> ោ, េ + ី -> ើ, េ + ៅ -> ៅ, េ + ៀ -> ៀ
    cleaned = cleaned.replace('\u17C1\u17B6', '\u17C4')  # េ + ា -> ោ
    cleaned = cleaned.replace('\u17C1\u17B8', '\u17BE')  # េ + ី -> ើ
    cleaned = cleaned.replace('\u17C1\u17B7', '\u17BE')  # េ + ិ -> ើ
    cleaned = cleaned.replace('\u17C1\u17C5', '\u17C5')  # េ + ៅ -> ៅ
    cleaned = cleaned.replace('\u17C1\u17C0', '\u17C0')  # េ + ៀ -> ៀ
    
    # 8. Remove spurious spaces between Khmer characters, coeng, and vowels/diacritics
    # (a) Space between any Khmer character and a dependent vowel, coeng, or diacritic
    cleaned = re.sub(r'(?<=[\u1780-\u17D2])\s+(?=[\u17B4-\u17D3])', '', cleaned)
    # (b) Space after Coeng (U+17D2) before a sub-consonant
    cleaned = re.sub(r'(?<=\u17D2)\s+(?=[\u1780-\u17B3])', '', cleaned)
    # (c) Space before Bantoc (់) or Nikahit (ំ)
    cleaned = re.sub(r'\s+(?=[\u17C6\u17CB])', '', cleaned)
    
    # 9. Normalize Unicode canonically (NFC)
    cleaned = unicodedata.normalize('NFC', cleaned)
    
    # 10. OCR cluster and coeng corrections
    # (a) Triple clusters where coeng-to is misread as duplicate coeng-ro (ក្រ្រ -> ក្ត្រ)
    cleaned = re.sub(r'ក្រ្រ', 'ក្ត្រ', cleaned)
    # (b) Vocabulary normalization for Sokhpheaktra
    cleaned = re.sub(r'ភ[ី៍]ក្ត្រ', 'ភ័ក្ត្រ', cleaned)
    # (c) Deduplicate duplicate coeng of the exact same consonant
    cleaned = re.sub(r'(\u17D2([\u1780-\u17B3]))\u17D2\2', r'\1', cleaned)
    # (d) Recover missing base consonant when word starts with coeng-ka (្ក -> ក្រ, e.g. ក្រវិល)
    cleaned = re.sub(r'(^|\s)\u17D2ក', r'\1ក្រ', cleaned)
    # (e) Vocabulary normalization for Van Cleef / clip (ឃ្លឹប / ឃ្លឺប -> ឃ្លីប)
    cleaned = re.sub(r'ឃ្ល[ឹឺ]ប', 'ឃ្លីប', cleaned)
    # (f) Strip stray leading punctuation, colons, or orphan dependent vowels from OCR crop margins
    cleaned = re.sub(r'^[:\sៈ|/\\-]+', '', cleaned)
    cleaned = re.sub(r'^[\u17B4-\u17D1\u17D3]+', '', cleaned)
    # (g) Dictionary normalization for ledger/bill (បញ្ឍី / បញ្ហី -> បញ្ជី)
    cleaned = re.sub(r'បញ្[ឍហ][ីឺ]', 'បញ្ជី', cleaned)

    # 11. Collapse any resulting multiple whitespace (preserve single spacing between words/numbers)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned).strip()
    
    return cleaned
