# Telefon ekrani rasmlari (qo'ng'iroq / qo'ng'iroq tugadi / bosh ekran) -> PNG, 750x1560
# python3 -I screens.py <chiqish_papka>
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/assets/screens"; os.makedirs(OUT, exist_ok=True)
W, H = 750, 1560
FD = "/usr/share/fonts/opentype/inter/"
F = lambda s, w="Bold": ImageFont.truetype(FD + f"Inter-{w}.otf", s)
def bg(top=(18, 40, 70), bot=(6, 10, 20)):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=tuple(int(a * (1 - t) + b * t) for a, b in zip(top, bot)))
    return im
def status(d):
    d.text((60, 40), "7:12", font=F(34, "SemiBold"), fill="white")
    d.rounded_rectangle((W - 140, 46, W - 80, 72), 7, outline="white", width=3); d.rectangle((W - 136, 50, W - 98, 68), fill="white")
    d.ellipse((W / 2 - 60, 30, W / 2 + 60, 80), fill="black")                 # kamera oroli
    d.rectangle((W - 210, 62, W - 200, 72), fill="white"); d.rectangle((W - 195, 55, W - 185, 72), fill="white"); d.rectangle((W - 180, 48, W - 170, 72), fill="white")
def avatar(d, cy, letter="D"):
    d.ellipse((W / 2 - 110, cy - 110, W / 2 + 110, cy + 110), fill=(90, 120, 170))
    d.text((W / 2, cy), letter, font=F(120), fill="white", anchor="mm")
def call(timer, ended=False):
    im = bg((20, 45, 80) if not ended else (40, 40, 48)); d = ImageDraw.Draw(im); status(d)
    # yoniq fonar belgisi (yuqori o'ng burchakda) — yashirin ishora
    if not ended:
        d.ellipse((W - 66, 96, W - 40, 122), fill=(255, 210, 60))
    avatar(d, 420)
    d.text((W / 2, 610), "Do'stim", font=F(70), fill="white", anchor="mm")
    d.text((W / 2, 690), "Qo'ng'iroq tugadi" if ended else timer, font=F(40, "Medium"), fill=(200, 210, 225), anchor="mm")
    labels = ["ovozsiz", "klaviatura", "karnay"]
    for i, lb in enumerate(labels):
        x = W / 2 + (i - 1) * 220
        d.ellipse((x - 70, 960, x + 70, 1100), fill=(255, 255, 255, 40) if False else (60, 72, 92))
        d.text((x, 1135), lb, font=F(28, "Medium"), fill=(200, 205, 215), anchor="mm")
    d.ellipse((W / 2 - 85, 1260, W / 2 + 85, 1430), fill=(235, 50, 45) if not ended else (120, 40, 40))
    # trubka belgisi
    d.rounded_rectangle((W / 2 - 50, 1330, W / 2 + 50, 1362), 14, fill="white")
    return im
call("00:24").save(f"{OUT}/call.png")
call("", ended=True).save(f"{OUT}/ended.png")
im = bg(); d = ImageDraw.Draw(im); status(d)
d.text((W / 2, 300), "7:12", font=F(190, "SemiBold"), fill="white", anchor="mm")
d.text((W / 2, 430), "Dushanba, 16-noyabr", font=F(40, "Medium"), fill=(220, 225, 235), anchor="mm")
im.save(f"{OUT}/lock.png")
print("ok", OUT)
