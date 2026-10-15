"""Uzbek text normalization for the MMS-TTS (Cyrillic) model: Latin -> Cyrillic, numbers -> words."""
import re

ONES = ["", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
TENS = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]


def num_to_uz(n: int) -> str:
    if n == 0:
        return "nol"
    parts = []
    for value, name in ((10 ** 9, "milliard"), (10 ** 6, "million"), (1000, "ming")):
        if n >= value:
            parts.append(f"{num_to_uz(n // value)} {name}")
            n %= value
    if n >= 100:
        parts.append(f"{ONES[n // 100]} yuz")
        n %= 100
    if n >= 10:
        parts.append(TENS[n // 10])
        n %= 10
    if n:
        parts.append(ONES[n])
    return " ".join(parts)


VOWELS = set("aeiouаеиоуўэюяё")
DIGRAPHS = [("o'", "ў"), ("g'", "ғ"), ("sh", "ш"), ("ch", "ч"), ("yo", "ё"), ("yu", "ю"), ("ya", "я"), ("ye", "е")]
SINGLE = dict(zip("abdfghijklmnpqrstuvxyzcw", "абдфгҳижклмнпқрстувхйзсв"))


def latin_to_cyrillic(text: str) -> str:
    text = re.sub(r"[‘’ʻʼ`´]", "'", text.lower())
    out, i = [], 0
    while i < len(text):
        two = text[i:i + 2]
        hit = next((c for d, c in DIGRAPHS if two == d), None)
        if hit:
            out.append(hit)
            i += 2
            continue
        ch = text[i]
        if ch == "e":
            prev = out[-1] if out else " "
            out.append("э" if (prev == " " or prev in VOWELS) else "е")
        elif ch == "o":
            out.append("о")
        elif ch == "'":
            out.append("ъ")
        else:
            out.append(SINGLE.get(ch, ch))
        i += 1
    return "".join(out)


def normalize_cyr(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\d+", lambda m: " " + num_to_uz(int(m.group())) + " ", text)
    text = latin_to_cyrillic(text)
    text = re.sub(r"[^а-яёўғқҳ ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


if __name__ == "__main__":
    for t in ["Assalomu alaykum! Bugun o'zbekistonda havo yaxshi.", "G'alaba, shahar, choy, yoshlik, ekran, 2026-yil", "Ташкент"]:
        print(t, "->", normalize_cyr(t))
