import re

from unidecode import unidecode


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\r\n\t]", " ", text)
    return text.strip()


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    text = clean_text(text)
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_quantity(text: str) -> tuple[int, str]:
    patterns = [
        r"(\d+)\s*(?:un(?:idade)?s?|pcs?|pecas?)\b",
        r"c/?(\d+)\s*(?:un(?:idade)?s?)?\b",
        r"(?:caixa|cx|pack|pct)\s*(?:c/?)?\s*(\d+)",
        r"(\d+)\s*(?:x|X)\s*\d+",
        r"^(\d+)\s+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            qty = int(match.group(1))
            if 1 <= qty <= 1000:
                return qty, text

    return 1, text


def remove_quantity_from_name(name: str, quantity: int) -> str:
    if quantity <= 1:
        return name
    patterns = [
        rf"\b{quantity}\s*(?:un(?:idade)?s?|pcs?|pecas?)\b",
        rf"c/?{quantity}\s*(?:un(?:idade)?s?)?\b",
        rf"(?:caixa|cx|pack|pct)\s*(?:c/?)?\s*{quantity}\b",
    ]
    result = name
    for pattern in patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return clean_text(result)
