#!/usr/bin/env python3
"""More YouTube/VK/Rutube/X material — legally: generate permission-request letters.

Collects the best "discovery only" candidates (platform videos whose licence is unknown /
standard) from verified.json and writes reports/permission_requests.md with one ready-to-send
message per channel (uz / ru / en), listing exactly which videos and time ranges you would
like to use. When the owner agrees, add the URL to manual_urls.txt with `license=permission`
and the video is downloaded and credited automatically.

Usage: python scripts/permission_requests.py --project <slug> [--per-scene 2]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, log, project_dir, read_json, setup_logging  # noqa: E402

LETTER = {
    "uz": ("Assalomu alaykum, {owner}!\n\nMen «{title}» nomli ta'limiy tarixiy hujjatli video tayyorlayapman. "
           "Kanalingizdagi quyidagi videolardan qisqa parchalarni (har biri 3–8 soniya) manbani ekranda va video "
           "tavsifida ko'rsatgan holda ishlatishga ruxsat bera olasizmi?\n\n{items}\n\n"
           "Ekrandagi yozuv: «Manba: {platform} / {owner}». Rozilik bildirsangiz, javob xatingizni ruxsat sifatida saqlab qo'yaman.\n\nHurmat bilan,\n[Ismingiz, kanal havolasi]"),
    "ru": ("Здравствуйте, {owner}!\n\nЯ готовлю образовательный исторический документальный ролик «{title}». "
           "Можно ли использовать короткие фрагменты (3–8 секунд каждый) из следующих ваших видео с указанием "
           "источника в кадре и в описании?\n\n{items}\n\nПодпись в кадре: «Источник: {platform} / {owner}». "
           "Ваш ответ я сохраню как подтверждение разрешения.\n\nС уважением,\n[Имя, ссылка на канал]"),
    "en": ("Hello {owner},\n\nI am producing an educational historical documentary, \"{title}\". "
           "May I use short excerpts (3–8 seconds each) from the following videos of yours, credited on screen "
           "and in the description?\n\n{items}\n\nOn-screen credit: \"Source: {platform} / {owner}\". "
           "I will keep your reply as the record of permission.\n\nBest regards,\n[Name, channel link]"),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--per-scene", type=int, default=2)
    ap.add_argument("--config")
    a = ap.parse_args(argv)
    setup_logging()
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    sb = read_json(pdir / "storyboard.json")
    ver = read_json(pdir / "verified.json")
    lang = sb.get("language", "uz")
    by_owner: dict[tuple[str, str], list[dict]] = {}
    for sid, d in ver.items():
        picks = [c for c in d.get("video", []) if c["license"]["risk"] >= 3 and c.get("download_method") == "ytdlp"
                 and not any("anachronism" in f for f in c.get("flags", []))][: a.per_scene]
        for c in picks:
            owner = c.get("handle") or c.get("author") or "?"
            by_owner.setdefault((c["source_label"], owner), []).append(dict(c, scene_id=sid))
    out = [f"# Permission requests — {sb['title']}", "",
           "Send each message via the channel's contact/e-mail/comment. When permission arrives add to manual_urls.txt:",
           "`URL | license=permission | author=@owner | note=permission e-mail YYYY-MM-DD | scene=s00X`", ""]
    for (platform, owner), items in sorted(by_owner.items(), key=lambda x: -len(x[1])):
        uniq: dict[str, list] = {}
        for c in items:
            uniq.setdefault(c["page_url"], [c["title"], []])[1].append(c["scene_id"])
        items = list(uniq)
        lst = "\n".join(f"- {t} — {u} (scenes {', '.join(sc)})" for u, (t, sc) in uniq.items())
        out += [f"## {platform} / {owner} ({len(items)} videos)", "", "```",
                LETTER.get(lang, LETTER["en"]).format(owner=owner, title=sb["title"], items=lst, platform=platform),
                "```", ""]
    f = pdir / "reports" / "permission_requests.md"
    f.write_text("\n".join(out), encoding="utf-8")
    log.info("%d channels, %d videos -> %s", len(by_owner), sum(map(len, by_owner.values())), f)
    print(f)


if __name__ == "__main__":
    main()
