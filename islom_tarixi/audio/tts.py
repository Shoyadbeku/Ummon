# O‘zbekcha diktor ovozi: edge-tts (uz-UZ-SardorNeural), past tembr.
# Ishga tushirish: SSL_CERT_FILE=/root/.ccr/ca-bundle.crt python3 tts.py
import asyncio, json, os, edge_tts
PITCH = "-9Hz"
async def main():
    os.makedirs("vo", exist_ok=True)
    for seg in json.load(open("vo_matn.json")):
        c = edge_tts.Communicate(seg["text"], "uz-UZ-SardorNeural", rate=seg.get("rate", "+0%"),
                                 pitch=PITCH, proxy=os.environ.get("HTTPS_PROXY"))
        await c.save(f"vo/{seg['id']}.mp3")
asyncio.run(main())
