import re
import unicodedata

from app.util.unaccent import unaccent


def sanitize_filename(filename: str, strip_accent: bool = False) -> str:
    if strip_accent:
        sanitized = unaccent(filename)
    else:
        sanitized = unicodedata.normalize("NFKC", filename)
    sanitized = re.sub(r"\(.*\)", "", sanitized)
    sanitized = re.sub(r"[^\w\s-]", "", sanitized.lower())
    sanitized = re.sub(r"[-\s]+", "-", sanitized).strip("-_")

    return sanitized
