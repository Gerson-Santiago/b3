import unicodedata


def normalize_alias(value: str) -> str:
    text = str(value or "").replace("\ufeff", "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())


def build_lookup(aliases):
    lookup = {}
    for canonical, labels in (aliases or {}).items():
        for label in labels:
            lookup[normalize_alias(label)] = canonical
    return lookup


__all__ = ["normalize_alias", "build_lookup"]
