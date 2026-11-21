"""Uzbek (Latin) text normalisation for TTS: numbers, dates, percents, currencies, units."""
import re

ONES = ["", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
TENS = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]
SCALES = [(10**12, "trillion"), (10**9, "milliard"), (10**6, "million"), (1000, "ming")]
MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def _below_1000(n: int) -> str:
    parts = []
    h, r = divmod(n, 100)
    if h:
        parts.append(("bir " if h == 1 else ONES[h] + " ") + "yuz")
    t, o = divmod(r, 10)
    if t:
        parts.append(TENS[t])
    if o:
        parts.append(ONES[o])
    return " ".join(p.strip() for p in parts if p)


def num_words(n: int) -> str:
    if n == 0:
        return "nol"
    if n < 0:
        return "minus " + num_words(-n)
    parts = []
    for val, name in SCALES:
        q, n = divmod(n, val)
        if q:
            parts.append(("" if (q == 1 and name == "ming") else num_words(q) + " ") + name)
    if n:
        parts.append(_below_1000(n))
    return " ".join(p.strip() for p in parts)


def ordinal(n: int) -> str:
    w = num_words(n)
    return w + ("nchi" if w[-1] in "aeiou" else "inchi")


def _decimal(s: str) -> str:
    whole, frac = re.split(r"[.,]", s)
    frac = frac.rstrip("0") or "0"
    return f"{num_words(int(whole))} butun {num_words(int(frac))}" + (" o'ndan" if len(frac) == 1 else " yuzdan" if len(frac) == 2 else " mingdan")


def normalize(text: str) -> str:
    t = text.replace("ʻ", "'").replace("‘", "'").replace("’", "'").replace("ʼ", "'").replace("`", "'")
    t = t.replace("—", ", ").replace("–", "-").replace("«", "").replace("»", "").replace("“", "").replace("”", "").replace('"', "")
    # dates: 21-noyabr / 21 noyabr
    t = re.sub(r"\b(\d{1,2})[- ](%s)" % "|".join(MONTHS), lambda m: f"{ordinal(int(m.group(1)))} {m.group(2)}", t, flags=re.I)
    # years: 2026-yil / 2026 yilda
    t = re.sub(r"\b(\d{4})[- ]?(yil\w*)", lambda m: f"{ordinal(int(m.group(1)))} {m.group(2)}", t)
    # ordinals: 5-o'rin, 3-chi
    t = re.sub(r"\b(\d+)-(?=[a-z'])", lambda m: ordinal(int(m.group(1))) + " ", t)
    # money and units
    t = re.sub(r"\$\s?(\d[\d.,]*)\s?(mlrd|mln|milliard|million|ming)?\b\.?", lambda m: f"{m.group(1)} {m.group(2) or ''} dollar", t)
    t = re.sub(r"(\d[\d\s.,]*)\s?€", r"\1 yevro", t)
    t = re.sub(r"(\d)\s?%", r"\1 foiz", t)
    t = re.sub(r"(\d)\s?mlrd\b\.?", r"\1 milliard", t)
    t = re.sub(r"(\d)\s?mln\b\.?", r"\1 million", t)
    t = re.sub(r"(\d)\s?ming\b", r"\1 ming", t)
    t = re.sub(r"(\d)\s?kVt[·\.]?soat", r"\1 kilovatt soat", t)
    t = re.sub(r"(\d)\s?km\b", r"\1 kilometr", t)
    t = re.sub(r"(\d)\s?°C", r"\1 daraja", t)
    # thousands separators "1 250 000" / "1,250,000"
    t = re.sub(r"(?<=\d)[  ,](?=\d{3}\b)", "", t)
    # decimals then integers
    t = re.sub(r"\b\d+[.,]\d+\b", lambda m: _decimal(m.group(0)), t)
    t = re.sub(r"\b\d+\b", lambda m: num_words(int(m.group(0))), t)
    return re.sub(r"\s+", " ", t).strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


if __name__ == "__main__":
    for s in ["21-noyabr kuni 350 kVt·soatgacha oshirildi.", "Narx 12,5% ga o'sdi, ya'ni 1 250 000 so'm.", "2026-yilda $4,2 mlrd investitsiya.", "3-o'rinda."]:
        print(s, "->", normalize(s))
