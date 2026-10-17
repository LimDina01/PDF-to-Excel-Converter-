"""
Cross-Platform Surgical OCR Utility for Khmer Text
Supports Windows & Ubuntu Linux.
Uses Tesseract OCR only on targeted bounding boxes for remarks containing Khmer text.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
from banks.khmer_utils import clean_khmer_text

_TESSERACT_PATH = None
_OCR_CHECKED = False


def get_tesseract_path():
    """
    Finds the Tesseract executable on the current system.
    Cross-platform: Works on Ubuntu Linux (/usr/bin/tesseract) and Windows.
    """
    global _TESSERACT_PATH, _OCR_CHECKED
    if _OCR_CHECKED:
        return _TESSERACT_PATH

    _OCR_CHECKED = True
    
    # 1. Check if 'tesseract' is in PATH (standard on Ubuntu Linux and customized Windows PATH)
    which_path = shutil.which("tesseract")
    if which_path:
        _TESSERACT_PATH = which_path
        return _TESSERACT_PATH

    # 2. Check standard Windows default directories
    if os.name == "nt":
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                _TESSERACT_PATH = p
                return _TESSERACT_PATH

    _TESSERACT_PATH = None
    return None


def is_ocr_available() -> bool:
    """Returns True if Tesseract executable is found on the system."""
    return get_tesseract_path() is not None


def ocr_crop(pil_image: Image.Image) -> str:
    """
    Runs Tesseract on a small cropped PIL image using -l khm+eng.
    Uses PSM 7 (treat image as single line of text) for maximum speed and accuracy.
    """
    tesseract_bin = get_tesseract_path()
    if not tesseract_bin:
        return ""

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
        temp_path = Path(temp.name)

    try:
        pil_image.save(str(temp_path))
        cmd = [
            tesseract_bin,
            str(temp_path),
            "stdout",
            "-l", "khm+eng",
            "--psm", "7"
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"Warning: OCR snippet failed: {e}")
        return ""
    finally:
        temp_path.unlink(missing_ok=True)


def ocr_khmer_snippet(page_img, x0: float, top: float, x1: float, bottom: float, pad: float = 3.0, scale: float = 3.0) -> str:
    """
    Crops a Khmer bounding box from the rendered page image and returns cleaned OCR text.
    """
    if page_img is None or not is_ocr_available():
        return ""
        
    crop_box = (
        max(0, int((x0 - pad) * scale)),
        max(0, int((top - pad) * scale)),
        min(page_img.width, int((x1 + pad) * scale)),
        min(page_img.height, int((bottom + pad) * scale))
    )
    cropped = page_img.crop(crop_box)
    raw_ocr = ocr_crop(cropped)
    if raw_ocr:
        return clean_khmer_text(raw_ocr)
    return ""


def process_desc_words(desc_words, get_page_img, use_ocr=True) -> str:
    """
    Processes words in the description/remark column of a line.
    If the line has no Khmer text, returns pure digital text immediately (0.00s).
    If the line has Khmer / missing font glyphs, surgically crops the Khmer segment
    and enhances it with Tesseract OCR while preserving English prefixes.
    """
    if not desc_words:
        return ""
        
    line_has_khmer = any(
        any(0x1780 <= ord(c) <= 0x17FF or c in '\x00\ufffe\ufffd' for c in w['text'])
        for w in desc_words
    )
    
    if not line_has_khmer or not use_ocr or not is_ocr_available():
        return " ".join(clean_khmer_text(w['text']) for w in desc_words) + " "
        
    eng_tokens = []
    khm_words = []
    for w in desc_words:
        t = w['text']
        if any(0x1780 <= ord(c) <= 0x17FF or c in '\x00\ufffe\ufffd' for c in t):
            khm_words.append(w)
        else:
            eng_tokens.append(t)
            
    if not khm_words:
        return " ".join(w['text'] for w in desc_words) + " "
        
    kx0 = min(w['x0'] for w in khm_words)
    ktop = min(w['top'] for w in khm_words)
    kx1 = max(w['x1'] for w in khm_words)
    kbottom = max(w['bottom'] for w in khm_words)
    
    img = get_page_img() if get_page_img else None
    ocr_res = ocr_khmer_snippet(img, kx0, ktop, kx1, kbottom) if img else ""
    
    if not ocr_res:
        ocr_res = " ".join(clean_khmer_text(w['text']) for w in khm_words)
        
    prefix = (" ".join(eng_tokens) + " ") if eng_tokens else ""
    return prefix + ocr_res + " "
