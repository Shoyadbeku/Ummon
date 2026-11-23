# YouTube yuklab olish hisoboti

Barcha sonlar shu sessiyada haqiqatda bajarilgan ishga asoslangan.

| Ko'rsatkich | Soni |
|---|---|
| YouTube qidiruv so'rovlari (o'zbek mavzusi bo'yicha ingliz/ispan tillarida) | **29** |
| Qidiruv natijalari (jami / takrorlanmagan videolar) | **216 / 187** |
| Sarlavha, kanal va davomiylik bo'yicha ko'rib chiqilgan videolar | **187** |
| Yuklab olish uchun tanlangan videolar | **34** |
| snapyt.app orqali muvaffaqiyatli yuklab olingan | **33** |
| Boshqa usul orqali olingan | **0** |
| Kadrma-kadr (contact sheet) tekshirilgan videolar | **33** |
| Mos deb topilib, yakuniy montajda ishlatilgan | **29** |
| Yakuniy montajdagi YouTube kadrlari (shot) | **172** |

## Yuklab olish usuli
1. YouTube qidiruvi `yt-dlp --flat-playlist "ytsearch8:..."` bilan bajarildi. Bu faqat ro'yxat olish, yuklab olish emas.
2. To'g'ridan-to'g'ri yuklab olish (yt-dlp) ishlamadi. YouTube bulut serverini **"Sign in to confirm you're not a bot"** xabari bilan to'sdi.
3. Shu sababli har bir video **https://snapyt.app** orqali olindi. Jarayon headless Chromium (Playwright) skripti bilan avtomatlashtirildi (`snapdl.js`): havola joylashtiriladi → preview sahifasi ochiladi → eng yuqori sifat tanlanadi → fayl saqlanadi.
4. Birinchi o'tishda skript sifat yorlig'ini noto'g'ri o'qidi ("★ 360p"), shuning uchun hammasi 360p bo'lib tushdi. Xato tuzatildi va zamonaviy videolar (intervyular, joylar, treylerlar) snapyt'ning "HD merge" funksiyasi orqali **1080p/720p**da qayta yuklandi (24 ta video).
5. 1972-yilgi arxiv filmlar YouTube'da faqat 240p–480p sifatda mavjud, shuning uchun ular shu sifatda olindi.

## Foydalanish huquqi
- Birorta videoda qayta foydalanish litsenziyasi (Creative Commons va h.k.) **yo'q**. Barchasi standart YouTube litsenziyasida.
- Siz ko'rsatma berganingizdek, **fair use** tamoyili asosida har bir videodan faqat qisqa parchalar olindi: bitta kadr o'rtacha 4–5 soniya, bitta manbadan ko'pi bilan bir necha parcha. Parchalar hujjatli sharh kontekstida, o'zbekcha izoh va manba yozuvi bilan ishlatildi. Ovozi o'chirilgan.
- Fair use AQSh huquqiy tamoyili. U kafolat emas va boshqa mamlakatlarda farq qilishi mumkin. YouTube Content ID ayrim parchalar (ayniqsa AP Archive, Netflix, BBC) uchun da'vo (claim) qo'yishi mumkin.
- snapyt.app orqali yuklab olish YouTube foydalanish shartlariga ziddir. Bu qadam sizning aniq ko'rsatmangiz bilan bajarildi.

## Yuklab olinmagan / ishlatilmagan videolar
| Video | Sabab |
|---|---|
| `Ec1GG6dq1Wc` (survivors announced moment) | snapyt.app preview sahifasi 2 marta yuklanmadi (90 s timeout) |
| `K_gKRCtlwfc` (Mountain Discovery) | **Rad etildi**: kadrlar AI yordamida chizilgan illyustratsiyalar, haqiqiy footage emas |
| `AxwloQQ1XA4` (24 Horas, vertikal) | Rad etildi: ustiga grafika yozilgan; o'sha 1972 TVN kadrlari `dHbEiZ-Im0s`dan toza holda olindi |
| `SGTaPeTfU1s` (Old Christians 2024 o'yini) | Rad etildi: zamonaviy jamoa, 1972 o'yinchilari emas |
| `wy-5WpNg5zo` (DiFilm, Algorta/Fernández/Parrado) | Tekshirildi, lekin ishlatilmadi: kadrdagi shaxslarni ism bilan aniq ajratib bo'lmadi |
| `yc6qBp23Emc` (Santiago drone) | Ishlatilmadi: Santyago xaritada ko'rsatildi |

To'liq ro'yxat (URL, kanal, timestamp): `YouTube_Footage_Sources.csv`.
