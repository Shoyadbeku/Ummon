"""Uzbek text normalization for the MMS-TTS (Cyrillic) model: Latin -> Cyrillic, numbers -> words."""
import re

from common import num_to_uz

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
