import unicodedata

def normalize_text(s: str) -> str:
    """Normalize bullets, quotes, and spacing for consistent downstream parsing."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("•", "-").replace("●", "-").replace("‣", "-")
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("\xa0", " ")
    return s.strip()
