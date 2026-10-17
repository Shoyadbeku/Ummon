# Mening ovozim — LoRA bilan o'qitilgan o'zbekcha TTS

Bazaviy model: [YourTTS](https://github.com/coqui-ai/TTS) (VITS, ko'p tilli, 16 kHz).
Unga foydalanuvchi ovozida LoRA adapter (rank 16, ~2.2M parametr) o'qitilgan:
matn kodlovchi, davomiylik bashoratchisi, flow va HiFi-GAN dekoderidagi barcha Conv1d/Linear qatlamlari.

## Pipeline
1. **Segmentlash + transkripsiya** — Silero VAD + Whisper (sherpa-onnx), `uz` tili.
   Whisper o'zbekchani yomon tanigani uchun transkriptlar qo'lda tozalangan, noaniq segmentlar tashlab yuborilgan.
2. **LoRA o'qitish** — `train_lora.py` (CPU, GAN yo'qotishlari: mel + KL + davomiylik + adversarial).
3. **Sayt** — `app.py` (FastAPI) + `static/index.html`.

## Ishga tushirish
```bash
pip install -r requirements.txt
python train_lora.py --base <your_tts_dir> --data train.json --embed_wavs wavs/*.wav --out out --steps 1200 --bs 4
VOICE_BASE=<your_tts_dir> VOICE_ADAPTER=out/lora_adapter.pt VOICE_SPEAKER=out/speaker.pt \
  uvicorn app:app --host 0.0.0.0 --port 8000
```
`train.json` — `[{"wav": "...16kHz mono.wav", "text": "o'zbekcha matn"}]`.
Kirill yozuvi va raqamlar avtomatik lotin/so'zga aylantiriladi (`common.normalize_uz`).
