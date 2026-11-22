# Ummon Diktor: OmniVoice voice design

O'zbekcha faktlar va ma'lumot beruvchi videolar uchun maxsus **erkak diktor ovozi**.
Ovoz [OmniVoice](https://huggingface.co/k2-fsa/OmniVoice) (k2-fsa) modelining voice design rejimida yaratilgan.

**Ovoz tavsifi:** jarangdor, past tembrli, o'rta yoshli erkak; aniq va tiniq talaffuz, ishonch uyg'otadigan diktor uslubi.

## Qanday ishlaydi

1. **Dizayn** (`python diktor.py dizayn`). OmniVoice'ga ovoz tavsifi beriladi
   (`male, middle-aged, low pitch` va yana 2 ta yaqin variant). Har biri uchun bir nechta nomzod yaratiladi.
   Har bir nomzod o'zbekcha ASR ([navai-uz/whisper-small-uzbek](https://huggingface.co/navai-uz/whisper-small-uzbek)) bilan qayta
   tinglanadi. Eng kam xato (CER) bilan o'qigan, ovozi past va qalin nomzod tanlanadi.
   U `ovozlar/diktor.pt` bo'lib saqlanadi va keyin har safar **aynan shu ovoz** chiqadi.
2. **O'qish** (`python diktor.py ayt`). Matn quyidagi bosqichlardan o'tadi:
   - **Normallash** (`uz_matn.py`): raqamlar, foiz, yillar, kasr sonlar, birliklar va qisqartmalar so'z bilan yoziladi.
     Masalan, `2026-yil` → «ikki ming yigirma oltinchi yil», `8,1 mlrd` → «sakkiz butun o'ndan bir milliard».
   - Matn gaplarga bo'linadi va har bir gap diktor ovozida yaratiladi.
   - **Adashmaslik tekshiruvi**: har bir gap ASR bilan qayta tinglanadi. Xato 8% dan oshsa, gap qayta yaratiladi
     (3 tagacha urinish) va eng to'g'ri varianti olinadi.
   - **Radio ishlovi** (ffmpeg): ko'krak jarangi (+120 Hz), so'z aniqligi (+3.5 kHz), kompressor va -16 LUFS.
     Natija YouTube, Reels va Shorts uchun tayyor 48 kHz WAV fayl bo'ladi.

## O'rnatish

```bash
python -m venv venv && . venv/bin/activate
pip install torch torchaudio            # GPU bo'lsa CUDA versiyasini o'rnating
pip install omnivoice soundfile transformers
# ffmpeg ham kerak: sudo apt install ffmpeg
```

## Ishlatish

```bash
# Diktor ovozida o'qitish (tayyor ovoz: ovozlar/diktor.pt)
python diktor.py ayt "Bilasizmi? Yer yuzida 8 milliarddan ortiq odam yashaydi." -o fakt.wav
python diktor.py ayt -f namuna_fakt.txt -o video_ovoz.wav

# Sozlamalar
#   --tezlik 0.95     sekinroq va salobatliroq (1.05 tezroq)
#   --pauza 0.5       gaplar orasidagi pauza
#   --tekshirmaslik   ASR tekshiruvisiz, tezroq
#   --xom             radio ishlovisiz

# Ovozni qaytadan loyihalash (boshqa nomzodlar bilan)
python diktor.py dizayn -n 6
```

CPU'da 10 soniyalik ovoz taxminan 1 daqiqada tayyor bo'ladi, GPU'da esa bir necha soniyada.

## O'z ovozingizni klonlash

```bash
# 5-20 soniyalik toza bo'lak va unda aytilgan aniq matn kerak
python diktor.py klon yozuv.wav --boshi 0.6 --oxiri 15.6 --matn "Bo'lakda aytilgan so'zlar..."
python diktor.py ayt --ovoz mening_ovozim -f matn.txt -o video.wav
```

`--matn` berilmasa, matn ASR bilan olinadi, lekin uning xatolari klon sifatini pasaytiradi.
Klon `ovozlar/mening_ovozim.pt` ga saqlanadi va repozitoriyga qo'shilmaydi (`.gitignore`).
Faqat o'z ovozingizni yoki ruxsat bergan odamning ovozini klonlang.

## Fayllar

```
diktor.py              dizayn va o'qish
uz_matn.py             o'zbekcha matn normallashtirgich (raqam → so'z)
namuna_fakt.txt        sinov matni
ovozlar/diktor.pt      tanlangan diktor ovozi (OmniVoice VoiceClonePrompt)
ovozlar/diktor_namuna.wav   shu ovozning namunasi
ovozlar/natijalar.tsv  barcha nomzodlar bali (CER, F0)
namunalar/             tayyor namunalar (mp3)
```

## Litsenziya

OmniVoice kodi Apache 2.0 litsenziyasida. **Model og'irliklari esa CC-BY-NC litsenziyasida**, ya'ni
ulardan faqat notijoriy maqsadda foydalanish mumkin. Pullik reklama yoki mijoz uchun buyurtma ishlarida
ishlatishdan oldin litsenziyani tekshiring.
