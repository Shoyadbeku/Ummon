#!/usr/bin/env python3
"""Steps 7-8: find the original source, verify licence, link health and
historical plausibility of the best candidates of every scene.

For each scene the top-N video and image candidates are checked:
  * dead links (page + media)                       -> rejected
  * archive items resolved to a real file (IA, LoC)
  * platform videos (YouTube/Rutube/VK/...)         -> full yt-dlp metadata; only an explicit
                                                       Creative Commons licence makes them usable
  * Yandex/Google hits                              -> original page analysed; Wikimedia pages get
                                                       their real licence; others stay "unknown"
  * licence risk vs config.licensing.max_allowed_risk
  * anachronism / AI-reconstruction flags from search scoring

Writes <project>/verified.json and reports/license_report.{json,md}.

Usage: python scripts/verify_license.py --project <slug> [--top 8] [--no-network]
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Http, domain_of, load_config, log, project_dir, read_json, setup_logging, write_json  # noqa: E402
from licenses import classify, credit_line  # noqa: E402

PLATFORM_DOMAINS = ("youtube.com", "youtu.be", "rutube.ru", "vk.com", "vkvideo.ru", "reddit.com", "x.com",
                    "twitter.com", "facebook.com", "fb.watch", "mover.uz", "ok.ru", "dailymotion.com", "vimeo.com")


def verify_one(c: dict, cfg: dict, http: Http, network: bool) -> dict:
    c = dict(c)
    reasons: list[str] = []
    lic_cfg = cfg["licensing"]
    monetized = cfg["project"].get("channel_monetized", True)
    if network:
        # resolve archive items to real files
        try:
            if c["provider"] == "internet_archive" and not c.get("media_url"):
                from providers.archives import InternetArchive
                InternetArchive(cfg, http).resolve(c)
            elif c["provider"] == "library_of_congress" and (c["media_type"] == "video" or not c.get("media_url")):
                from providers.archives import LibraryOfCongress
                LibraryOfCongress(cfg, http).resolve(c)
        except Exception as e:  # noqa: BLE001
            reasons.append(f"resolve_failed: {str(e)[:120]}")

        dom = domain_of(c["page_url"])
        # platform video: read real licence from platform metadata (no download)
        if c.get("download_method") == "ytdlp" and c["license"]["risk"] >= 3 and not c.get("extra", {}).get("manual"):
            try:
                from providers.platforms import ytdlp_json
                info = ytdlp_json(c["page_url"], flat=False, timeout=60)
                lic = info.get("license") or ""
                c["license_raw"] = lic or c.get("license_raw", "")
                c["license"] = classify(lic, "", c["provider"], monetized)
                c["height"] = info.get("height") or c.get("height", 0)
                c["width"] = info.get("width") or c.get("width", 0)
                c["duration"] = info.get("duration") or c.get("duration", 0)
                c["author"] = info.get("uploader") or c.get("author", "")
                if not lic:
                    reasons.append("platform_licence_not_open (standard licence)")
            except Exception as e:  # noqa: BLE001
                reasons.append(f"platform_metadata_failed: {str(e)[:120]}")
        # search engine hit: look at original page
        if c.get("extra", {}).get("found_via"):
            if "commons.wikimedia.org" in dom or "wikipedia.org" in dom:
                try:
                    from providers.archives import WikimediaCommons
                    info = WikimediaCommons(cfg, http).license_for_page(c["page_url"])
                    if info:
                        c["license_raw"] = info["license_raw"]
                        c["license"] = classify(info["license_raw"], info["license_url"], "wikimedia_commons", monetized)
                        c["author"] = info["author"] or c.get("author", "")
                        c["media_url"] = info["media_url"] or c["media_url"]
                        c["source_label"] = "Wikimedia Commons"
                except Exception as e:  # noqa: BLE001
                    reasons.append(f"commons_lookup_failed: {str(e)[:100]}")
            else:
                reasons.append(f"original page {dom}: licence must be checked manually")
        # link health
        ok, status, final = http.head_ok(c["page_url"])
        if not ok and status not in (0, 403, 429):
            reasons.append(f"dead_page:{status}")
        if c.get("media_url") and c.get("download_method") == "http":
            ok2, st2, _ = http.head_ok(c["media_url"])
            if not ok2 and st2 not in (0, 403, 429):
                reasons.append(f"dead_media:{st2}")
    # decisions
    risk = c["license"]["risk"]
    status = "approved"
    if any(r.startswith(("dead_page", "dead_media")) for r in reasons):
        status = "rejected"
    elif c.get("download_method") == "http" and not c.get("media_url"):
        status = "rejected"
        reasons.append("no_downloadable_file")
    elif risk > lic_cfg["max_allowed_risk"]:
        if (c["media_type"] == "video" and lic_cfg.get("allow_fair_use_clips") and risk == 4
                and c.get("download_method") == "ytdlp"):
            status = "fair_use_review"
            c["max_clip_sec"] = lic_cfg.get("fair_use_max_clip_sec", 6)
            reasons.append("copyrighted: only short transformative excerpt, needs human review")
        else:
            status = "rejected"
            reasons.append(f"licence_risk_{risk}: {c['license']['label']}")
    if lic_cfg.get("require_original_page") and not c.get("page_url"):
        status = "rejected"
        reasons.append("no_original_page")
    if "possible_ai_or_reconstruction" in c.get("flags", []):
        reasons.append("AI/reconstruction: must be labelled, never presented as archive")
    if any(f.startswith("anachronism") for f in c.get("flags", [])):
        if status == "approved":
            status = "review"
        reasons.append("anachronism suspected")
    if "pre_photographic_video: must be present-day/documentary footage, verify" in c.get("flags", []):
        reasons.append("period has no film record: use only as labelled present-day/museum footage")
        if status == "approved" and not c.get("extra", {}).get("manual"):
            status = "review"
    if c["media_type"] == "video" and c.get("height") and c["height"] < cfg["search"]["min_video_height"]:
        reasons.append(f"low_resolution:{c['height']}p")
        c["score"] = c.get("score", 0) - 1.5
    if c["media_type"] == "image" and c.get("width") and c["width"] < cfg["search"]["min_image_width"]:
        reasons.append(f"low_resolution:{c['width']}px")
        c["score"] = c.get("score", 0) - 1.5
    c["status"] = status
    c["verify_notes"] = reasons
    c["credit"] = credit_line(c, cfg["project"]["language"], cfg["overlay"]["source_prefix"])
    return c


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--top", type=int, default=8, help="candidates per scene and media type to verify")
    ap.add_argument("--no-network", action="store_true", help="licence rules only (offline)")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    http = Http(cfg)
    verified: dict[str, dict[str, list]] = {}
    for mt in ("video", "image"):
        f = pdir / f"candidates_{mt}.json"
        if not f.exists():
            log.warning("no %s candidates (%s)", mt, f.name)
            continue
        cands = read_json(f)
        jobs = []
        seen: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=6) as ex:
            for sid, lst in cands.items():
                for c in lst[: a.top]:
                    key = c.get("media_url") or c["page_url"]
                    if key in seen:  # same asset in several scenes: verify once
                        jobs.append((sid, None, key))
                        continue
                    fut = ex.submit(verify_one, c, cfg, http, not a.no_network)
                    seen[key] = fut
                    jobs.append((sid, fut, key))
            for sid, fut, key in jobs:
                res = (fut or seen[key]).result()
                res = dict(res, scene_id=sid)
                verified.setdefault(sid, {}).setdefault(mt, []).append(res)
    for sid in verified:
        for mt in verified[sid]:
            verified[sid][mt].sort(key=lambda c: ({"approved": 0, "review": 1, "fair_use_review": 2}.get(c["status"], 9), -c["score"]))
    write_json(pdir / "verified.json", verified)
    # report
    rows = [c for s in verified.values() for l in s.values() for c in l]
    summary = {}
    for c in rows:
        summary[c["status"]] = summary.get(c["status"], 0) + 1
    write_json(pdir / "reports" / "license_report.json", {"summary": summary, "items": [
        {k: c.get(k) for k in ("scene_id", "id", "provider", "media_type", "title", "page_url", "status",
                                "verify_notes", "credit")} | {"license": c["license"]["label"], "risk": c["license"]["risk"]}
        for c in rows]})
    md = ["# Licence verification report", "", f"Summary: {summary}", "",
          "| Scene | Type | Status | Risk | Licence | Source | Notes |", "|---|---|---|---|---|---|---|"]
    for c in rows:
        md.append(f"| {c['scene_id']} | {c['media_type']} | {c['status']} | {c['license']['risk']} | "
                  f"{c['license']['label']} | [{c['source_label']}]({c['page_url']}) | {'; '.join(c['verify_notes'])[:160]} |")
    (pdir / "reports" / "license_report.md").write_text("\n".join(md), encoding="utf-8")
    log.info("verification: %s", summary)
    print(pdir / "verified.json")


if __name__ == "__main__":
    main()
