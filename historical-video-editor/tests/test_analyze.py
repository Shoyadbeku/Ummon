from analyze_script import analyse, find_dates, find_entities, media_era, split_scenes, norm

SCRIPT = """# Kirish
*[Vizual: Registon]*

Samarqand. Buyuk Ipak yo'lining yuragi. 1336-yilda Kesh yaqinida Amir Temur tug'ildi.

# Jang
1402-yilda Anqara yaqinida Boyazid bilan jang bo'ldi. Ammo bu jang tarixni o'zgartirdi va Usmonli saltanati larzaga keldi.
"""


def test_split_and_notes():
    sc = split_scenes(norm(SCRIPT))
    assert len(sc) == 2
    assert sc[0]["heading"] == "Kirish"
    assert sc[0]["notes"] == ["Vizual: Registon"]


def test_dates():
    d = find_dates("1336-yilda va XIV asrda, а также в 1402 году; 300 askar")
    assert 1336 in d["years"] and 1402 in d["years"]
    assert 300 not in d["years"]
    assert 14 in d["centuries"]
    assert find_dates("329 mil. avv. Iskandar")["years"] == [-329]


def test_entities_multilingual():
    assert "Timur" in find_entities(norm("Тамерлан и Самарканд"), "persons")
    assert "Samarkand" in find_entities(norm("Тамерлан и Самарканд"), "places")
    assert "Bayezid I" in find_entities(norm("Boyazid bilan jang"), "persons")
    assert "battle" in find_entities(norm("Boyazid bilan jang"), "terms")


def test_media_era():
    assert media_era(1400) == "pre_photographic"
    assert media_era(1880) == "early_photography"
    assert media_era(1920) == "silent_film"
    assert media_era(1942) == "sound_film_bw"


def test_analyse_full(cfg):
    sb = analyse(SCRIPT, "Amir Temur", cfg, duration=60)
    assert abs(sb["total_duration"] - 60) < 0.5
    s1, s2 = sb["scenes"]
    assert s1["period"]["media_era"] == "pre_photographic"
    assert any(e["type"] == "lower_third" for e in s1["effects"])
    assert any(e["type"] == "impact_cut" for e in s2["effects"])          # "Ammo"
    assert any(e["type"] == "date_card" and e["text"] == "1402" for e in s2["effects"])
    assert "film" in s1["exclude_terms"]                                   # anachronism guard
    assert s1["queries"]["en"] and s1["queries"]["ru"] and s1["queries"]["uz"]
    assert s1["start"] == 0 and abs(s2["start"] - s1["duration"]) < 0.01
