# Storyboard / EDL for "O'zbekiston U-17 vs Ispaniya" news-documentary edit.
# Times in seconds on the voice-over timeline (voice.wav, 310.51 s).
TOTAL = 310.51
FPS = 25

SRC = {
    "GB5": ("GB5JtRbhnCE", "Spain v Fiji | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "AP4": ("AP4HSMzeZKc", "Spain v China PR | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "TR7": ("tr7SqpfS2VM", "Morocco v Spain | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "PMA": ("PmA4T3ex-IM", "Cote d'Ivoire v Uzbekistan | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "JPL": ("JpLx_06N90E", "Uzbekistan v Jamaica | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "3L2": ("3l2KcKSIhvY", "Uzbekistan v Italy | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "QIS": ("QiS1_GGqOUQ", "Romania v Cameroon | HIGHLIGHTS | FIFA U-17 World Cup 2026", "FIFA"),
    "XOW": ("xOwpfxtyktA", "Italy vs Uzbekistan Highlights | FIFA U-17 World Cup Qatar 2025", "FIFA"),
    "O5F": ("o5fxQFaoBII", "Croatia vs Uzbekistan Highlights | FIFA U-17 World Cup Qatar 2025", "FIFA"),
    "JTP": ("_JtpV_eNKOY", "England vs Uzbekistan | World Cup U-17 Indonesia 2023 (re-upload)", "Subang Football"),
    "THY": ("_tHyvzuJJBc", "Japan knock out holders after dramatic finish | Japan - Uzbekistan | AFC U17 Asian Cup", "AFC Asian Cup"),
    "6YC": ("6ycFZfaUS5c", "U-17: Ahead of Uzbekistan vs. Jamaica | Axborot 24", "O'zbekiston 24"),
    "AWR": ("AwRsRYjlLQo", "Uzbekistan lift the Asian U17 trophy | Uzbekistan vs. Saudi Arabia | AFC U17 Asian Cup", "AFC Asian Cup"),
}

# crop boxes (x, y, w, h) in 1920x1080 source pixels to remove re-uploader watermarks / TV frames
CROP = {
    "JTP": (77, 72, 998, 562),
    "6YC": (422, 20, 1075, 605),
}

def ts(s):
    if isinstance(s, (int, float)):
        return float(s)
    m, sec = s.split(":")
    return int(m) * 60 + float(sec)

# (t0, t1, src, src_in, look, note)
#   look: n=normal, d=dark/dramatic, a=archive(2023), b=blurred background for graphics, k=black
SCENES = [
    (0.00, 1.70, "GB5", "1:59.6", "d", "Ispaniya gol nishonlashi"),
    (1.70, 3.60, "AP4", "0:54.0", "d", "Ispaniya jarima zarbasi goli"),
    (3.60, 5.80, "TR7", "1:49.5", "d", "Ispaniya o'yinchilari"),
    (5.80, 8.40, "PMA", "0:11.3", "n", "O'zbekiston muxlislari bayroq bilan"),
    (8.40, 9.25, "GB5", "0:15.0", "d", "Ispaniya o'yinchisi yaqin plan"),
    (9.25, 10.30, None, 0, "k", "Qora ekran: SAVOL BITTA"),
    (10.30, 11.55, "JPL", "1:35.5", "n", "O'zbek o'yinchilari jilmayib"),
    (11.55, 13.30, "TR7", "0:05.6", "d", "Ispaniya 10-raqam orqadan"),
    (13.30, 17.80, "PMA", "0:05.4", "n", "O'zbekiston jamoasi davra qurib"),
    (17.80, 21.50, "3L2", "0:06.6", "n", "O'zbek muxlisi bayroq bilan"),
    (21.50, 24.10, "AP4", "0:02.6", "n", "Ispaniya saf tortgan"),
    (24.10, 26.80, "JPL", "0:05.4", "n", "Yosh muxlis 'UZBEKISTAN' sharfi bilan"),
    (26.80, 31.00, "JTP", "0:56.0", "a", "ARXIV 2023: o'zbek o'yinchisi"),
    (31.00, 34.00, "JTP", "0:16.0", "a", "ARXIV 2023: stadion umumiy plan"),
    (34.00, 35.60, "TR7", "0:09.0", "b", "BO'LIM: 01 PLEY-OFFGA YO'L"),
    (35.60, 38.20, "XOW", "0:00.0", "n", "Doha, Aspire Zone havodan"),
    (38.20, 40.60, "AP4", "0:00.0", "n", "Stadion, kechki payt"),
    (40.60, 49.30, "QIS", "0:12.0", "b", "GRAFIKA: turnir formati"),
    (49.30, 55.60, "3L2", "0:00.0", "n", "Jamoalar maydonga chiqmoqda + E guruh"),
    (55.60, 59.30, "PMA", "0:00.0", "n", "Muxlislar: O'zbekiston va Kot-d'Ivuar"),
    (59.30, 61.80, "PMA", "0:20.3", "n", "Kot-d'Ivuar gol nishonlashi"),
    (61.80, 64.20, "PMA", "1:50.3", "d", "O'zbek darvozaboni, mag'lubiyat"),
    (64.20, 66.60, "JPL", "0:20.5", "n", "O'zbek o'yinchisi"),
    (66.60, 69.40, "JPL", "0:00.0", "n", "O'zbekiston - Yamayka, saf"),
    (69.40, 73.20, "JPL", "1:01.8", "n", "Sadirjonov gol uradi"),
    (73.20, 76.00, "JPL", "0:57.4", "n", "11-raqam Sadirjonov"),
    (76.00, 80.70, "JPL", "1:14.4", "n", "O'zbekiston hujumi"),
    (80.70, 82.60, "JPL", "0:35.6", "n", "O'zbek o'yinchisi"),
    (82.60, 85.00, "3L2", "0:02.6", "n", "Italiya muxlislari"),
    (85.00, 87.30, "3L2", "0:23.6", "n", "Italiya gol nishonlashi"),
    (87.30, 89.60, "3L2", "1:55.0", "n", "Yakuniy hisob 1:3"),
    (89.60, 94.60, "3L2", "0:40.0", "b", "GRAFIKA: E guruh jadvali"),
    (94.60, 97.50, "QIS", "0:00.0", "d", "Kechki stadion"),
    (97.50, 100.10, "QIS", "0:02.3", "n", "Ruminiya muxlislari"),
    (100.10, 103.00, "QIS", "0:06.3", "d", "Ruminiya o'yinchisi"),
    (103.00, 105.00, "QIS", "1:40.8", "n", "Kamerun qo'shimcha vaqtda gol"),
    (105.00, 107.60, "QIS", "1:53.3", "d", "Ruminiya o'yinchilari tushkun"),
    (107.60, 111.90, "XOW", "0:40.6", "n", "O'zbek muxlislari tribunada"),
    (111.90, 116.60, "PMA", "0:59.4", "n", "O'zbek o'yinchilari quvonchi"),
    (116.60, 120.40, "TR7", "0:08.6", "b", "BO'LIM: 02 RAQIB - ISPANIYA"),
    (120.40, 123.20, "AP4", "0:05.6", "n", "Ispaniya - Xitoy"),
    (123.20, 126.20, "TR7", "0:09.0", "n", "Marokash - Ispaniya"),
    (126.20, 129.60, "GB5", "0:41.4", "n", "Fiji darvozaboni"),
    (129.60, 133.50, "GB5", "2:14.4", "d", "Fiji o'yinchisi tiz cho'kkan"),
    (133.50, 137.60, "TR7", "1:43.6", "n", "Ispaniya darvozaboni"),
    (137.60, 140.80, "TR7", "0:46.6", "n", "Ispaniya o'yini"),
    (140.80, 144.40, "AP4", "1:17.4", "n", "Ispaniya to'p nazorati"),
    (144.40, 147.70, "TR7", "0:41.6", "n", "Ispaniya dribling"),
    (147.70, 151.80, "TR7", "1:25.6", "d", "Ispaniya hujumchisi darvozaga"),
    (151.80, 155.50, "JTP", "0:05.6", "b", "BO'LIM: 03 UNUTILGAN O'YIN"),
    (155.50, 162.40, "JTP", "0:11.6", "a", "ARXIV 2023: Indoneziya"),
    (162.40, 171.20, "JTP", "0:29.6", "b", "GRAFIKA: 2023 O'zbekiston 2:2 Ispaniya"),
    (171.20, 173.40, "JTP", "1:59.6", "a", "ARXIV 2023: Angliya - O'zbekiston"),
    (173.40, 179.00, "JTP", "3:43.6", "a", "ARXIV 2023: O'zbekiston ikkinchi goli"),
    (179.00, 184.60, "JTP", "0:59.6", "b", "GRAFIKA: Fransiya 1:0 O'zbekiston"),
    (184.60, 187.90, "JTP", "2:20.6", "a", "ARXIV 2023: o'zbek hujumi"),
    (187.90, 191.40, "JTP", "3:05.6", "a", "ARXIV 2023: o'zbek o'yinchisi"),
    (191.40, 198.30, "XOW", "0:41.6", "b", "GRAFIKA: tarixiy natijalar"),
    (198.30, 202.40, "O5F", "0:05.4", "n", "QATAR 2025: O'zbekiston jamoasi"),
    (202.40, 204.60, "O5F", "1:38.8", "n", "Xorvatiya bilan penaltilar"),
    (204.60, 206.60, "O5F", "1:55.6", "n", "O'zbekiston muxlislari nishonlaydi"),
    (206.60, 208.70, "XOW", "1:53.0", "d", "Italiya 3:2 O'zbekiston"),
    (208.70, 212.30, "6YC", "0:12.0", "b", "BO'LIM: 04 TAHLIL"),
    (212.30, 216.40, "JPL", "1:08.6", "n", "O'zbekiston goli"),
    (216.40, 221.20, "PMA", "0:58.8", "n", "O'zbek o'yinchilari nishonlaydi"),
    (221.20, 225.00, "AWR", "1:02.8", "n", "O'zbek hujumchisi, Osiyo kubogi"),
    (225.00, 229.40, "3L2", "0:26.0", "n", "Italiya hujumi, darvoza oldi"),
    (229.40, 233.00, "PMA", "0:22.8", "n", "Kot-d'Ivuar goli"),
    (233.00, 237.30, "3L2", "0:43.6", "n", "Jarima maydoni"),
    (237.30, 244.50, "XOW", "0:41.0", "n", "O'zbek muxlislari"),
    (244.50, 247.10, "3L2", "0:06.6", "n", "O'zbek muxlisi bayroq bilan"),
    (247.10, 250.60, "AWR", "1:11.5", "n", "Stadion, muxlislar (Osiyo kubogi)"),
    (250.60, 256.60, "PMA", "0:00.4", "n", "Muxlislar bayroqlar bilan"),
    (256.60, 262.50, "3L2", "1:07.6", "n", "Tribuna"),
    (262.50, 266.30, "JPL", "0:56.8", "n", "Sadirjonov"),
    (266.30, 270.30, "3L2", "1:43.6", "n", "O'zbek o'yinchisi yuguradi"),
    (270.30, 272.10, "O5F", "0:59.6", "n", "O'zbek o'yinchisi yaqin plan"),
    (272.10, 276.30, "THY", "0:08.6", "n", "AFC: Yaponiya safi"),
    (276.30, 279.90, "THY", "1:40.6", "n", "AFC: O'zbekiston hujumi"),
    (279.90, 282.30, "THY", "1:59.6", "n", "AFC: penaltilar seriyasi"),
    (282.30, 288.30, "AP4", "0:00.0", "b", "GRAFIKA: o'yin kuni"),
    (288.30, 290.30, "AP4", "1:56.6", "n", "Ispaniya jamoa surati"),
    (290.30, 292.50, "O5F", "1:52.6", "n", "O'zbek o'yinchisi quchoqlanadi"),
    (292.50, 295.70, "JTP", "2:08.6", "b", "GRAFIKA: 2023 - 2:2"),
    (295.70, 298.90, "AWR", "0:14.6", "n", "O'zbekiston o'yinchilari madhiya paytida"),
    (298.90, 302.00, "AWR", "1:50.8", "n", "O'zbek o'yinchisi"),
    (302.00, 305.20, "O5F", "1:55.4", "n", "Muxlislar"),
    (305.20, 308.30, "PMA", "0:11.0", "n", "Bayroq"),
    (308.30, 310.51, "PMA", "0:00.0", "n", "Muxlislar, yakun"),
]

for s in SCENES:
    assert s[1] > s[0]
for a, b in zip(SCENES, SCENES[1:]):
    assert abs(a[1] - b[0]) < 1e-6, (a, b)
assert abs(SCENES[-1][1] - TOTAL) < 1e-6
