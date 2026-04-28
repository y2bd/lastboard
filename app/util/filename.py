import re
import unicodedata


def sanitize_filename(filename: str) -> str:
    sanitized = unicodedata.normalize("NFKC", filename)
    sanitized = re.sub(r"\(.*?\)", "", sanitized)
    sanitized = re.sub(r"[^\w\s-]", "", sanitized.lower())
    sanitized = re.sub(r"[-\s]+", "-", sanitized).strip("-_")

    return sanitized
