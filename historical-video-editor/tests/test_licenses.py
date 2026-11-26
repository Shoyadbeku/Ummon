from licenses import classify, credit_line




def test_public_domain_variants():
    for raw in ("Public domain", "PD-US", "CC0", "No known restrictions on publication.",
                "http://rightsstatements.org/vocab/NoC-US/1.0/", "https://creativecommons.org/publicdomain/mark/1.0/"):
        assert classify(raw)["risk"] == 0, raw


def test_cc_family():
    assert classify("CC BY 4.0")["code"] == "cc-by"
    assert classify("CC BY-SA 3.0")["risk"] == 2
    assert classify("", "https://creativecommons.org/licenses/by-sa/4.0/")["share_alike"] is True
    nc = classify("CC BY-NC 4.0", monetized=True)
    assert nc["risk"] == 3 and nc["commercial_ok"] is False
    assert classify("CC BY-NC 4.0", monetized=False)["risk"] == 2
    assert classify("CC BY-ND 2.0", monetized=False)["risk"] == 3  # no derivatives -> never editable


def test_unknown_and_arr():
    assert classify("")["risk"] == 4
    assert classify("All rights reserved")["risk"] == 4
    assert classify("Standard YouTube License")["risk"] == 4


def test_stock_providers():
    assert classify("", "", "pexels")["risk"] == 1
    assert classify("", "", "pixabay")["commercial_ok"]


def test_credit_line_languages():
    a = {"media_type": "video", "archival": True, "source_label": "Internet Archive", "author": "",
         "license": classify("Public Domain")}
    assert credit_line(a, "en") == "Archive footage: Internet Archive, Public Domain"
    assert credit_line(a, "uz").startswith("Arxiv kadrlari: Internet Archive")
    img = {"media_type": "image", "source_label": "Wikimedia Commons", "author": "John Doe",
           "license": classify("CC BY-SA 4.0")}
    assert credit_line(img, "uz") == "Manba: Wikimedia Commons / John Doe, CC BY-SA 4.0"
    x = {"media_type": "video", "source_label": "X", "handle": "@archive", "license": classify("")}
    assert credit_line(x, "en") == "Source: X / @archive"
