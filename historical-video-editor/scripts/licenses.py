"""License normalisation and risk scoring.

risk scale (config.licensing.max_allowed_risk):
  0  Public Domain / CC0 / "no known restrictions"           -> free to use
  1  CC BY, Pexels/Pixabay/Mixkit licence                     -> attribution / credit
  2  CC BY-SA                                                 -> attribution + share-alike caution
  3  CC BY-NC*, CC BY-ND*, editorial-only                     -> NOT for monetized channels / no edits
  4  unknown, all rights reserved, platform user uploads      -> do not use without permission
"""
from __future__ import annotations

import re

RIGHTS_FREE_PATTERNS = [
    r"public\s*domain", r"\bpd\b", r"pd-", r"cc0", r"cc-?zero", r"no known (copyright )?restrictions",
    r"publicdomain/mark", r"publicdomain/zero", r"no copyright",
    r"rightsstatements\.org/vocab/noc", r"not in copyright", r"общественное достояние", r"jamoat mulki",
]


def classify(license_raw: str | None = None, license_url: str | None = None, provider: str = "",
             monetized: bool = True) -> dict:
    raw = " ".join(x for x in (license_raw or "", license_url or "") if x).strip()
    low = raw.lower()
    out = {"code": "unknown", "label": license_raw or "Unknown", "url": license_url or "",
           "risk": 4, "commercial_ok": False, "modify_ok": False, "attribution_required": True,
           "share_alike": False}

    def setv(code, label, risk, commercial, modify, attrib, sa=False, url=None):
        out.update(code=code, label=label, risk=risk, commercial_ok=commercial, modify_ok=modify,
                   attribution_required=attrib, share_alike=sa)
        if url and not out["url"]:
            out["url"] = url

    if provider == "pexels":
        setv("pexels", "Pexels License", 1, True, True, False, url="https://www.pexels.com/license/")
        return out
    if provider == "pixabay":
        setv("pixabay", "Pixabay Content License", 1, True, True, False, url="https://pixabay.com/service/license-summary/")
        return out
    if provider == "mixkit":
        setv("mixkit", "Mixkit License", 1, True, True, False, url="https://mixkit.co/license/")
        return out
    if not low:
        return out
    if any(re.search(p, low) for p in RIGHTS_FREE_PATTERNS):
        code = "cc0" if ("cc0" in low or "zero" in low) else "pd"
        setv(code, "CC0" if code == "cc0" else "Public Domain", 0, True, True, False)
        return out
    m = re.search(r"(?:cc|creative\s*commons)[\s_-]*(?:attribution|by)?[\s_-]*((?:-?(?:by|sa|nc|nd))+)?[\s_-]*(\d\.\d)?", low)
    url_m = re.search(r"creativecommons\.org/licenses/([a-z-]+)/?(\d\.\d)?", low)
    parts = ""
    ver = ""
    if url_m:
        parts, ver = url_m.group(1), url_m.group(2) or ""
    elif re.search(r"\bcc[\s_-]?by|creative\s*commons|attribution", low):
        tokens = re.findall(r"\b(by|sa|nc|nd)\b", low.replace("-", " ").replace("_", " "))
        parts = "-".join(dict.fromkeys(tokens)) or "by"
        vm = re.search(r"(\d\.\d)", low)
        ver = vm.group(1) if vm else ""
    elif m and m.group(1):
        parts = m.group(1).strip("-")
    if parts:
        p = set(parts.split("-"))
        p.add("by")
        label = "CC " + "-".join(x.upper() for x in ("by", "nc", "nd", "sa") if x in p) + (f" {ver}" if ver else "")
        url = f"https://creativecommons.org/licenses/{'-'.join(x for x in ('by', 'nc', 'nd', 'sa') if x in p)}/{ver or '4.0'}/"
        if "nc" in p or "nd" in p:
            setv(label.replace(" ", "-", 1).lower(), label, 3 if monetized or "nd" in p else 2,
                 "nc" not in p, "nd" not in p, True, "sa" in p, url)
        elif "sa" in p:
            setv("cc-by-sa", label, 2, True, True, True, True, url)
        else:
            setv("cc-by", label, 1, True, True, True, False, url)
        return out
    if re.search(r"gfdl|gnu free documentation", low):
        setv("gfdl", "GFDL", 2, True, True, True, True)
        return out
    if re.search(r"editorial|news use only|fair use", low):
        setv("editorial", license_raw or "Editorial use only", 3, False, False, True)
        return out
    if re.search(r"all rights reserved|©|copyright|standard youtube license|youtube standard", low):
        setv("arr", license_raw or "All rights reserved", 4, False, False, True)
        return out
    return out


def credit_line(asset: dict, lang: str = "en", prefixes: dict | None = None) -> str:
    """Short on-screen credit, e.g. 'Source: Wikimedia Commons / John Doe, CC BY-SA 4.0'."""
    prefixes = prefixes or {"uz": "Manba", "ru": "Источник", "en": "Source"}
    pre = prefixes.get(lang, "Source")
    kind = asset.get("media_type")
    if kind == "video" and asset.get("archival"):
        pre = {"uz": "Arxiv kadrlari", "ru": "Архивные кадры", "en": "Archive footage"}.get(lang, pre)
    src = asset.get("source_label") or asset.get("provider", "")
    author = (asset.get("author") or "").strip()
    lic = asset.get("license", {})
    who = src
    if asset.get("handle"):
        who = f"{src} / {asset['handle']}"
    elif author and author.lower() not in src.lower() and len(author) < 40:
        who = f"{src} / {author}"
    tail = ""
    if lic.get("code") in ("pd", "cc0"):
        tail = "Public Domain" if lic.get("code") == "pd" else "CC0"
    elif lic.get("code", "").startswith("cc") or lic.get("code") == "gfdl":
        tail = lic.get("label", "")
    if asset.get("reconstruction"):
        tail = (tail + " · " if tail else "") + {"uz": "rekonstruksiya", "ru": "реконструкция", "en": "reconstruction"}.get(lang, "reconstruction")
    if asset.get("present_day"):
        tail = (tail + " · " if tail else "") + {"uz": "hozirgi ko'rinish", "ru": "наши дни", "en": "present day"}.get(lang, "present day")
    line = f"{pre}: {who}"
    return f"{line}, {tail}" if tail else line
