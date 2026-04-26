import unicodedata


def unaccent(x: str):
    # https://stackoverflow.com/a/517974/7966259
    return "".join(
        [c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c)]
    )
