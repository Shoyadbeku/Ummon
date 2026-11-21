"""Central configuration. Secrets are NEVER stored here: they come from env vars / files outside the repo."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent          # newsbot/
REPO = ROOT.parent
DATA = Path(os.environ.get("NEWSBOT_DATA", ROOT / "data"))   # gitignored: db, audio, renders
EPISODES = ROOT / "episodes"                           # episode.json files (committed) + assets (ignored)
REMOTION = ROOT / "remotion"
DB_PATH = DATA / "newsbot.sqlite"
VOICE_REF = REPO / "voices" / "boshlovchi_ayol.wav"
VOICE_REF_TEXT = (REPO / "voices" / "boshlovchi_ayol.txt")

TZ = ZoneInfo("Asia/Tashkent")
BRAND = os.environ.get("NEWSBOT_BRAND", "POMI.UZ")
USER_AGENT = "NewsVideoTool/1.0 (https://meta.wikimedia.org/wiki/User-Agent_policy) python-urllib"

# Daily schedule (Asia/Tashkent). region drives source selection and on-screen branding.
SLOTS = {
    "09:00": {"region": "uz",    "label": "O'zbekistonning eng dolzarb yangiliklari", "kicker": "O'ZBEKISTON"},
    "12:00": {"region": "world", "label": "Dunyoning eng muhim yangiliklari",        "kicker": "DUNYO"},
    "15:00": {"region": "world", "label": "Dunyo bo'ylab trenddagi yangiliklar",     "kicker": "DUNYO TRENDI"},
    "18:00": {"region": "uz",    "label": "O'zbekistondagi eng yangi xabarlar",      "kicker": "O'ZBEKISTON"},
    "20:00": {"region": "uz",    "label": "O'zbekiston: kechki yangiliklar",         "kicker": "KECHKI XABARLAR"},
}

# RSS feeds that were verified reachable from the production environment.
FEEDS = [
    # Uzbekistan
    {"name": "Kun.uz",      "url": "https://kun.uz/news/rss",                         "region": "uz",    "trust": 0.85},
    {"name": "Gazeta.uz",   "url": "https://www.gazeta.uz/uz/rss/",                   "region": "uz",    "trust": 0.85},
    {"name": "Daryo.uz",    "url": "https://daryo.uz/feed",                           "region": "uz",    "trust": 0.8},
    {"name": "UzA",         "url": "https://uza.uz/uz/rss",                           "region": "uz",    "trust": 0.9},
    # World
    {"name": "BBC World",   "url": "https://feeds.bbci.co.uk/news/world/rss.xml",     "region": "world", "trust": 0.95},
    {"name": "Al Jazeera",  "url": "https://www.aljazeera.com/xml/rss/all.xml",       "region": "world", "trust": 0.85},
    {"name": "The Guardian","url": "https://www.theguardian.com/world/rss",           "region": "world", "trust": 0.9},
    {"name": "Euronews",    "url": "https://www.euronews.com/rss",                    "region": "world", "trust": 0.85},
    {"name": "Google News", "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "region": "world", "trust": 0.7},
]

# Instagram (Graph API). Token is read from env IG_TOKEN or from the file in IG_TOKEN_FILE.
IG_USER_ID = os.environ.get("IG_USER_ID", "17841457665224605")
IG_TOKEN_FILE = os.environ.get("IG_TOKEN_FILE", str(Path.home() / ".config" / "newsbot" / "ig_token"))
GRAPH = "https://graph.facebook.com/v21.0"

# Publishing mode: "approval" (default, admin must confirm) or "auto".
PUBLISH_MODE = os.environ.get("NEWSBOT_PUBLISH_MODE", "approval")

for p in (DATA, EPISODES):
    p.mkdir(parents=True, exist_ok=True)
