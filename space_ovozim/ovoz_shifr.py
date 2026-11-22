"""Ovoz faylini parol bilan shifrlash (faqat Python standart kutubxonasi).

Space ochiq bo'lgani uchun undagi fayllarni har kim yuklab olishi mumkin. Ovoz fayli
(`ovoz.enc`) shifrlangan holda turadi va faqat PAROL secret bilan ochiladi.

    python ovoz_shifr.py shifrla mening_ovozim_tez.pt ovoz.enc PAROL
"""

import hashlib
import hmac
import os
import sys

BELGI = b"UMMONv1"


def _kalitlar(parol: str, tuz: bytes) -> tuple[bytes, bytes]:
    k = hashlib.pbkdf2_hmac("sha256", parol.encode(), tuz, 300_000, dklen=64)
    return k[:32], k[32:]


def _oqim(kalit: bytes, n: int) -> bytes:
    out = bytearray()
    i = 0
    while len(out) < n:
        out += hashlib.sha256(kalit + i.to_bytes(8, "big")).digest()
        i += 1
    return bytes(out[:n])


def shifrla(malumot: bytes, parol: str) -> bytes:
    tuz = os.urandom(16)
    k_shifr, k_imzo = _kalitlar(parol, tuz)
    shifr = bytes(a ^ b for a, b in zip(malumot, _oqim(k_shifr, len(malumot))))
    imzo = hmac.new(k_imzo, tuz + shifr, "sha256").digest()
    return BELGI + tuz + imzo + shifr


def och(paket: bytes, parol: str) -> bytes:
    if not paket.startswith(BELGI):
        raise ValueError("Bu Ummon ovoz fayli emas.")
    paket = paket[len(BELGI):]
    tuz, imzo, shifr = paket[:16], paket[16:48], paket[48:]
    k_shifr, k_imzo = _kalitlar(parol, tuz)
    if not hmac.compare_digest(imzo, hmac.new(k_imzo, tuz + shifr, "sha256").digest()):
        raise ValueError("Parol noto'g'ri yoki fayl buzilgan.")
    return bytes(a ^ b for a, b in zip(shifr, _oqim(k_shifr, len(shifr))))


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "shifrla":
        sys.exit(__doc__)
    _, _, kirish, chiqish, parol = sys.argv
    with open(kirish, "rb") as f, open(chiqish, "wb") as g:
        g.write(shifrla(f.read(), parol))
    print("Shifrlandi:", chiqish)
