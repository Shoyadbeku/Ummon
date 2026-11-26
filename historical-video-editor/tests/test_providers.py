
from common import Http
from providers.base import make_candidate
from providers.platforms import ManualUrls
from providers.search_engines import YandexImages, manual_search_links
from search_core import score_candidate, scene_queries


def test_yandex_xml_parser():
    xml = ("<response><results><doc><url>https://commons.wikimedia.org/wiki/File:A.jpg</url><title>A</title>"
           "<image-link>https://upload.wikimedia.org/a.jpg</image-link><original-width>3000</original-width>"
           "<original-height>2000</original-height><domain>commons.wikimedia.org</domain></doc></results></response>")
    out = YandexImages._parse_xml(xml)
    assert out[0]["pageUrl"].startswith("https://commons.wikimedia.org")
    assert out[0]["url"].endswith("a.jpg")


def test_manual_urls_images(tmp_path, cfg):
    f = tmp_path / "manual_urls.txt"
    f.write_text("# c\nhttps://example.org/photo.jpg | license=CC BY 4.0 | author=@someone | scene=s002\n"
                 "https://example.org/b.png | license=permission | note=email\n", encoding="utf-8")
    m = ManualUrls(cfg, Http(cfg))
    items = m.load(f)
    assert len(items) == 2
    assert items[0]["license"]["code"] == "cc-by" and items[0]["handle"] == "@someone" and items[0]["extra"]["scene"] == "s002"
    assert items[1]["license"]["label"] == "Used with permission" and items[1]["license"]["risk"] == 1


def test_scoring_prefers_relevant_open_material(cfg):
    scene = {"places": ["Samarkand"], "persons": ["Timur"], "terms": [], "period": {"start": 1336, "end": 1405},
             "exclude_terms": ["film", "photo"]}
    good = make_candidate("wikimedia_commons", "image", page_url="u1", title="Timur portrait Samarkand 1400",
                          license_raw="Public Domain", width=3000)
    bad = make_candidate("ytdlp_discovery", "video", page_url="u2", title="Tank film 1943", license_raw="")
    assert score_candidate(good, scene, "Timur portrait", cfg) > score_candidate(bad, scene, "Timur portrait", cfg)
    assert any(f.startswith("anachronism") for f in bad.get("flags", []))


def test_query_interleaving():
    sc = {"queries": {"en": ["a1", "a2"], "ru": ["b1"], "uz": ["c1", "c2"], "maps": ["m1"]}}
    q = scene_queries(sc, ["en", "ru", "uz"], "image", 4)
    assert q[0] == ("en", "m1") and ("ru", "b1") in q


def test_manual_links():
    d = manual_search_links("Amir Temur")
    assert "yandex.ru/images" in d["yandex_images"] and "mover.uz" in d["mover_uz"]


def test_anachronistic_year_is_flagged(cfg):
    scene = {"places": [], "persons": ["Timur"], "terms": [], "exclude_terms": [],
             "period": {"start": 1336, "end": 1405, "media_era": "pre_photographic"}}
    c = make_candidate("wikimedia_commons", "video", page_url="u", title="1940 Тимур и его команда.webm",
                       license_raw="Public Domain")
    score_candidate(c, scene, "Тимур", cfg)
    assert any("anachronism" in f for f in c["flags"])
    assert any(f.startswith("pre_photographic_video") for f in c["flags"])
