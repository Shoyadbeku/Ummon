"""Text-to-voice web site powered by the LoRA-trained voice."""
import os
import threading

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from synth import VoiceSynth

BASE = os.environ["VOICE_BASE"]          # YourTTS base model directory
ADAPTER = os.environ["VOICE_ADAPTER"]    # lora_adapter.pt
SPEAKER = os.environ["VOICE_SPEAKER"]    # speaker.pt
HERE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Mening ovozim")
synth = VoiceSynth(BASE, ADAPTER, SPEAKER)
lock = threading.Lock()


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    speed: float = Field(1.0, ge=0.5, le=2.0)


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


@app.post("/api/tts")
def tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(400, "Matn bo'sh")
    with lock:
        wav = synth.synthesize(req.text, req.speed)
    return Response(synth.to_wav_bytes(wav), media_type="audio/wav")
