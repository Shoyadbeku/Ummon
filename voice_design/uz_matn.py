"""O'zbekcha matnni ovozlashtirishga tayyorlash (lotin yozuvi).

TTS modeli raqam, foiz, qisqartma va belgilarni o'zi to'g'ri o'qiy olmaydi.
Shuning uchun ular oldindan so'z bilan yoziladi:

    "2026-yil"      -> "ikki ming yigirma oltinchi yil"
    "45%"           -> "qirq besh foiz"
    "3,5 km"        -> "uch butun o'ndan besh kilometr"
    "1 200 000 so'm" -> "bir million ikki yuz ming so'm"
"""

import re

BIRLAR = ["nol", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
ONLAR = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]
KATTA = [(10**12, "trillion"), (10**9, "milliard"), (10**6, "million"), (1000, "ming")]
KASR_NOMI = {1: "o'ndan", 2: "yuzdan", 3: "mingdan"}

BIRLIKLAR = {
    "km": "kilometr", "m": "metr", "sm": "santimetr", "mm": "millimetr",
    "kg": "kilogramm", "g": "gramm", "t": "tonna", "l": "litr",
    "km²": "kvadrat kilometr", "m²": "kvadrat metr", "km/soat": "kilometr soatiga",
    "mln": "million", "mlrd": "milliard", "trln": "trillion", "ming": "ming",
    "°C": "daraja", "°": "daraja", "$": "dollar", "€": "yevro",
}

QISQARTMALAR = {
    "va h.k.": "va hokazo", "h.k.": "hokazo", "mil. avv.": "milloddan avvalgi",
    "masalan,": "masalan,", "AQSH": "Amerika Qo'shma Shtatlari", "BMT": "Birlashgan Millatlar Tashkiloti",
    "O'zR": "O'zbekiston Respublikasi", "AI": "sun'iy intellekt", "sh.": "shahri", "y.": "yil",
}

# o' va g' uchun turli tutuq belgilari bitta ko'rinishga keltiriladi.
TUTUQ = re.compile(r"[‘’ʻʼ`´]")


def son_soz(n: int) -> str:
    """Butun sonni o'zbekcha so'z bilan yozadi: 1984 -> 'bir ming to'qqiz yuz sakson to'rt'."""
    if n < 0:
        return "minus " + son_soz(-n)
    if n < 10:
        return BIRLAR[n]
    qismlar = []
    for qiymat, nom in KATTA:
        if n >= qiymat:
            qismlar.append(f"{son_soz(n // qiymat)} {nom}")
            n %= qiymat
    if n >= 100:
        qismlar.append("yuz" if n // 100 == 1 else f"{BIRLAR[n // 100]} yuz")
        n %= 100
    if n >= 10:
        qismlar.append(ONLAR[n // 10])
        n %= 10
    if n:
        qismlar.append(BIRLAR[n])
    return " ".join(qismlar)


def tartib_soz(n: int) -> str:
    """Tartib son: 1 -> birinchi, 2 -> ikkinchi, 2026 -> ikki ming yigirma oltinchi."""
    soz = son_soz(n)
    return soz + ("nchi" if soz[-1] in "aeiou" else "inchi")


def _butun(s: str) -> int:
    return int(re.sub(r"[\s  .]", "", s))


def _kasr(butun: str, kasr: str) -> str:
    nom = KASR_NOMI.get(len(kasr))
    if not nom:
        return son_soz(_butun(butun)) + " butun " + " ".join(BIRLAR[int(c)] for c in kasr)
    return f"{son_soz(_butun(butun))} butun {nom} {son_soz(int(kasr))}"


# 1 200 000 yoki 1.200.000 kabi minglik ajratgichli sonlar ham qo'llanadi.
SON = r"\d{1,3}(?:[   .]\d{3})+(?!\d)|\d+"


_B = sorted((k for k in BIRLIKLAR if k not in "$€"), key=len, reverse=True)
BIRLIK = r"(?:\s*(" + "|".join(re.escape(k) for k in _B) + r")(?![\w²/]))?"


def _birlik(k):
    return " " + BIRLIKLAR[k] if k else ""


def normallash(matn: str) -> str:
    t = TUTUQ.sub("'", matn)
    t = t.replace("—", ", ").replace("–", "-").replace("…", "...")
    for k, v in QISQARTMALAR.items():
        t = re.sub(rf"(?<!\w){re.escape(k)}(?!\w)", v, t)

    # Yillar oralig'i: 1941-1945-yillar -> bir ming ... qirq birinchi - ... yillar
    t = re.sub(r"(\d+)\s*-\s*(\d+)\s*-\s*(yil\w*|asr\w*)",
               lambda m: f"{tartib_soz(int(m[1]))} va {tartib_soz(int(m[2]))} {m[3]}", t)
    # Tartib sonlar: 2026-yil, 5-sinf, XXI emas, 3-o'rin
    t = re.sub(r"(\d+)\s*-\s*(?=[a-zA-Z'])", lambda m: tartib_soz(int(m[1])) + " ", t)
    # Foiz: 45% yoki 3,5%
    t = re.sub(r"(\d+)[,.](\d+)\s*%", lambda m: _kasr(m[1], m[2]) + " foiz", t)
    t = re.sub(rf"({SON})\s*%", lambda m: son_soz(_butun(m[1])) + " foiz", t)
    # Valyuta: $500 -> besh yuz dollar
    t = re.sub(rf"([$€])\s*({SON})", lambda m: f"{son_soz(_butun(m[2]))} {BIRLIKLAR[m[1]]}", t)
    # O'nli kasr va butun sonlar, ortidan kelgan o'lchov birligi bilan birga: 3,5 km, 36,6°C
    t = re.sub(rf"(?<![\d.])(\d+),(\d{{1,3}})(?!\d){BIRLIK}", lambda m: _kasr(m[1], m[2]) + _birlik(m[3]), t)
    t = re.sub(rf"({SON}){BIRLIK}", lambda m: son_soz(_butun(m[1])) + _birlik(m[2]), t)
    # "20% ini", "8 mlrd dan" -> "foizini", "milliarddan": qo'shimchani so'zga ulash
    t = re.sub(r"\b(foiz|milliard|million|trillion|ming|kilometr|metr|dollar|daraja|kilogramm|tonna|litr) "
               r"(i|ini|ni|ga|da|dan|ning|lik|cha|gacha|ta)\b", r"\1\2", t)
    t = t.replace("+", " plyus ").replace("=", " teng ").replace("&", " va ")
    return re.sub(r"\s+", " ", t).strip()


if __name__ == "__main__":
    import sys

    print(normallash(" ".join(sys.argv[1:]) or "2026-yil 45% o'sish, 3,5 km, 1 200 000 so'm, $500, 1941-1945-yillar"))
