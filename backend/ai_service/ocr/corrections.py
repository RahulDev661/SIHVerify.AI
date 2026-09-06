"""
Shared MRZ OCR-correction utilities.

Previously this exact character-confusion map, and near-identical
helper functions, were copy-pasted across mrz_normalizer.py,
mrz_corrector.py and mrz_candidate.py. That's the single source of
truth now — the three modules import from here instead of keeping
their own copies, so a future fix to the confusion table only has to
happen in one place.
"""

import re


# Letters Tesseract commonly confuses with digits in the MRZ font.
OCR_TO_DIGIT = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}


def clean_mrz_text(text: str) -> str:
    """
    Upper-case and strip everything that isn't a valid MRZ
    character (A-Z, 0-9, '<').
    """

    text = text.upper()

    return re.sub(r"[^A-Z0-9<]", "", text)


def correct_char_to_digit(char: str) -> str:
    """
    Convert a single character into a digit using the OCR confusion
    map. Only apply this to characters in fields that must be
    numeric (dates, check digits) — never to name or nationality
    fields, which can legitimately contain the same letters.
    """

    char = char.upper()

    if char.isdigit():
        return char

    return OCR_TO_DIGIT.get(char, char)


def correct_digit_field(field: str) -> str:
    """Apply `correct_char_to_digit` across an entire field."""

    return "".join(correct_char_to_digit(char) for char in field)
