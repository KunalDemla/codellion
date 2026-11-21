import re
import unicodedata

def normalize_answer(value: str, case_sensitive=False) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip()
    if not case_sensitive:
        value = value.casefold()
    return re.sub(r"\s+", " ", value)
