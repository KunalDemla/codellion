import re
import unicodedata

def normalize_answer(value: str, case_sensitive=False) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip()
    if not case_sensitive:
        value = value.casefold()
    return re.sub(r"\s+", " ", value)


def is_single_typo(text: str, candidate: str) -> bool:
    """Detect one insertion, deletion, substitution, or adjacent swap."""
    if len(text) > len(candidate):
        text, candidate = candidate, text
    difference = len(candidate) - len(text)
    if difference > 1:
        return False
    index = next((i for i, (left, right) in enumerate(zip(text, candidate)) if left != right), len(text))
    if difference:
        return text[index:] == candidate[index + 1:]
    if index == len(text):
        return False
    return (text[index + 1:] == candidate[index + 1:]
            or (text[index:index + 2] == candidate[index:index + 2][::-1]
                and text[index + 2:] == candidate[index + 2:]))
