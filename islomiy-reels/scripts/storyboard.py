"""Storyboard: every shot is anchored to timestamps of the voice-over (seconds).

Fields per shot:
  t      -> start time in seconds (shot ends where the next one starts)
  src    -> 'mk:<id>'  Mixkit clip, 'wm:<key>' Wikimedia Commons video,
            'img:<key>' Wikimedia image (manuscript), 'gfx:<name>' pure motion graphics
  at     -> in-point inside the source clip (seconds)
  cx     -> horizontal focus for the 9:16 crop of a 16:9 source (0 = left, 1 = right)
  mv     -> camera move: pushIn | pullOut | panL | panR | rise | sink | drift | punch
  tr     -> transition INTO this shot: dissolve | cut | flash | zoom | dip | whip
  fx     -> extra layers: cracks, shake, gold, rays, dust, rain, glow, pattern, keys, lightning
  badge  -> optional verse reference (Arabic + Uzbek), not a subtitle
  sp     -> playback speed (<1 = slow motion)
  note   -> what is being said (editor's note, not rendered)
"""
import json, sys

END = 520.15

S = [
 # ---------------- HOOK ----------------
 dict(t=0.00, src='mk:2862', at=1.0, cx=.55, mv='punch', tr='cut', fx=['gold', 'rays'], note='Qorun...'),
 dict(t=1.35, src='mk:2861', at=1.5, cx=.45, mv='pushIn', tr='flash', fx=['gold'], note='boyligi bilan'),
 dict(t=2.55, src='mk:4149', at=2.0, cx=.62, mv='punch', tr='zoom', fx=['cracks', 'shake', 'dust'], note='yerga yutilgan inson'),
 dict(t=4.45, src='mk:52009', at=3.0, cx=.5, mv='pushIn', tr='dip', note='Tarixda shunday bir inson'),
 dict(t=7.00, src='img:ms1', mv='rise', tr='dissolve', fx=['glow', 'dust'], note="Qur'oni Karimda"),
 dict(t=9.90, src='gfx:keys', tr='flash', fx=['keys', 'gold', 'rays'], note='xazinalar kalitlari'),
 dict(t=12.60, src='mk:2865', at=2.0, cx=.5, mv='pushIn', tr='dissolve', fx=['gold'], note='kuchli kishilar jamoasiga'),
 dict(t=15.20, src='mk:28889', at=1.0, cx=.5, mv='pullOut', tr='whip', note='ulkan boyligi...'),
 dict(t=17.20, src='mk:4422', at=4.0, cx=.4, mv='drift', tr='dissolve', fx=['lightning'], note='halokatdan qutqarmadi'),
 dict(t=19.55, src='mk:2093', at=1.0, cx=.5, mv='sink', tr='cut', fx=['cracks', 'shake', 'dust'], note='yerga yuttirdi'),
 dict(t=23.30, src='mk:3458', at=2.0, cx=.5, mv='pushIn', tr='dip', note='Bu inson kim bo\'lgan?'),
 dict(t=25.20, src='mk:21612', at=1.0, cx=.5, mv='panR', tr='dissolve', note='boyligini qanday...'),
 dict(t=27.20, src='img:ms5', mv='panL', tr='dissolve', fx=['glow'], note='Nima sababdan Qur\'onda'),
 dict(t=31.40, src='mk:49878', at=2.0, cx=.5, mv='sink', tr='whip', note='bugungi insonlarga ogohlantirish'),
 # ---------------- KIM BO'LGAN ----------------
 dict(t=36.60, src='img:ms2', mv='pushIn', tr='dip', fx=['glow', 'pattern'], note='islomiy manbalarda Qorun'),
 dict(t=40.30, src='wm:wadirum', at=4.0, cx=.5, mv='panR', tr='dissolve', fx=['dust'], note='Muso a.s. davrida'),
 dict(t=43.30, src='img:ms1', mv='pullOut', tr='flash', fx=['glow', 'pattern'], badge=('سورة القصص ٧٦–٨٢', 'Qasas surasi, 76–82'), note='76–82-oyatlar'),
 dict(t=51.10, src='mk:2862', at=6.0, cx=.35, mv='panL', tr='dissolve', fx=['gold'], note='boyligi'),
 dict(t=53.40, src='mk:4285', at=2.0, cx=.45, mv='drift', tr='dissolve', note='qavmiga munosabati'),
 dict(t=55.20, src='mk:4060', at=3.0, cx=.5, mv='pushIn', tr='dissolve', note='kibrga berilishi'),
 dict(t=57.40, src='mk:4423', at=2.0, cx=.55, mv='drift', tr='cut', fx=['lightning'], note='qanday jazolangani'),
 dict(t=59.80, src='mk:40047', at=1.0, cx=.45, mv='pushIn', tr='dip', note='Avvalo kim bo\'lganini'),
 dict(t=62.90, src='img:ms7', mv='rise', tr='dissolve', fx=['glow'], badge=('سورة القصص ٧٦', 'Qasas surasi, 76'), note='Muso qavmidan'),
 dict(t=68.00, src='mk:4285', at=11.0, cx=.6, mv='panR', tr='dissolve', fx=['dust'], note='Bani Isroil'),
 dict(t=70.60, src='mk:21576', at=1.0, cx=.5, mv='sink', tr='dissolve', note='zulm qilgani'),
 dict(t=74.00, src='mk:3438', at=1.0, cx=.5, mv='pushIn', tr='dip', note='tafsir manbalarida'),
 dict(t=78.60, src='mk:21612', at=5.0, cx=.4, mv='panL', tr='dissolve', note='amakivachchasi rivoyati'),
 dict(t=82.70, src='img:ms3', mv='pushIn', tr='dissolve', fx=['glow'], note="Qur'on matnida ko'rsatilmagan"),
 dict(t=87.80, src='img:ms4', mv='pullOut', tr='dissolve', fx=['pattern'], note="qat'iy fakt emas"),
 dict(t=91.20, src='mk:4148', at=2.0, cx=.5, mv='rise', tr='dissolve', note='rivoyat sifatida'),
 # ---------------- BOYLIGI ----------------
 dict(t=94.70, src='mk:2861', at=4.0, cx=.5, mv='pushIn', tr='flash', fx=['gold'], note='boyligi haqidagi oyat'),
 dict(t=98.00, src='gfx:keys', tr='dissolve', fx=['keys', 'gold', 'rays'], badge=('سورة القصص ٧٦', 'Qasas surasi, 76'), note='kalitlari og\'irlik qilgan'),
 dict(t=102.00, src='mk:2862', at=3.0, cx=.7, mv='panR', tr='dissolve', fx=['gold'], note='xazinalar'),
 dict(t=105.00, src='mk:2865', at=8.0, cx=.45, mv='pullOut', tr='dissolve', fx=['gold'], note='kuchli kishilar'),
 dict(t=108.20, src='mk:28890', at=1.0, cx=.5, mv='pushIn', tr='dip', note='muhim jihat'),
 dict(t=110.50, src='mk:18263', at=1.0, cx=.5, mv='drift', tr='dissolve', note='qancha oltin, kumush'),
 dict(t=113.40, src='mk:18296', at=1.0, cx=.5, mv='pushIn', tr='dissolve', note='mol-mulk'),
 dict(t=116.80, src='mk:18302', at=3.0, cx=.5, mv='panL', tr='dissolve', note='dollar qiymatiga'),
 dict(t=120.00, src='mk:18247', at=0.5, cx=.5, mv='drift', tr='dissolve', note='eng boy inson'),
 dict(t=122.50, src='mk:18299', at=4.0, cx=.5, mv='sink', tr='dissolve', note='ishonchli asos yo\'q'),
 dict(t=126.00, src='mk:2889', at=1.0, cx=.5, mv='pushIn', tr='zoom', note='favqulodda katta boylik'),
 dict(t=130.40, src='mk:4311', at=1.0, cx=.55, mv='rise', tr='dissolve', fx=['rays'], note='Qur\'on tanqid qiladi'),
 dict(t=134.00, src='wm:mihrimah', at=270.0, cx=.5, mv='pushIn', tr='dissolve', fx=['rays'], note='qilgan ishlari sababli'),
 # ---------------- NASIHAT ----------------
 dict(t=138.40, src='wm:adhan_vertical', at=150.0, cx=.5, mv='drift', tr='dissolve', fx=['rays', 'dust'], note='qavmi nasihat qilgan'),
 dict(t=143.50, src='mk:4059', at=3.0, cx=.5, mv='pushIn', tr='dissolve', fx=['lightning'], note='haddan tashqari quvonib'),
 dict(t=147.80, src='mk:4081', at=8.0, cx=.62, mv='pushIn', tr='dip', sp=0.75, note='Alloh kibrlilarni sevmaydi'),
 dict(t=152.80, src='mk:1944', at=10.0, cx=.5, mv='rise', tr='dissolve', fx=['rays'], note='qanday foydalanish'),
 dict(t=157.30, src='img:ms6', mv='panR', tr='dissolve', fx=['glow'], badge=('سورة القصص ٧٧', 'Qasas surasi, 77'), note='77-oyat'),
 dict(t=160.50, src='mk:100831', at=0.0, cx=.5, mv='rise', tr='dissolve', sp=0.8, fx=['rays'], note='oxirat saodati'),
 dict(t=163.50, src='mk:1170', at=3.0, cx=.5, mv='drift', tr='dissolve', note='dunyodagi nasibasi'),
 dict(t=165.80, src='mk:101510', at=2.0, cx=.5, mv='panR', tr='dissolve', note='yaxshilik qilish'),
 dict(t=169.30, src='wm:kaaba_ramadan', at=66.0, cx=.52, mv='pushIn', tr='flash', fx=['rays'], note='islomda muhim o\'rin'),
 dict(t=174.00, src='mk:18263', at=6.0, cx=.5, mv='pushIn', tr='dissolve', note='halol boylik'),
 dict(t=178.60, src='wm:haram_timelapse', at=40.0, cx=.5, mv='drift', tr='dissolve', note='qanday topilishi, sarflanishi'),
 dict(t=182.40, src='mk:34372', at=0.5, cx=.5, mv='drift', tr='dissolve', fx=['rays'], note='qalbga ta\'siri'),
 dict(t=186.40, src='mk:28889', at=4.0, cx=.5, mv='pushIn', tr='dip', note='imkoniyat ham, sinov ham'),
 dict(t=190.60, src='mk:4422', at=10.0, cx=.6, mv='drift', tr='dissolve', fx=['lightning'], note="to'g'ri anglamagan"),
 # ---------------- JAVOBI ----------------
 dict(t=194.20, src='img:ms1', mv='panL', tr='flash', fx=['glow'], badge=('سورة القصص ٧٨', 'Qasas surasi, 78'), note='78-oyat'),
 dict(t=198.60, src='mk:4808', at=2.0, cx=.4, mv='pushIn', tr='dissolve', note="o'zimdagi ilm tufayli"),
 dict(t=203.20, src='mk:4196', at=2.0, cx=.5, mv='panR', tr='dissolve', note="qobiliyati va bilimi"),
 dict(t=208.60, src='mk:4096', at=1.0, cx=.6, mv='drift', tr='dip', fx=['dust'], note='avvalgi avlodlar'),
 dict(t=212.40, src='wm:wadirum2', at=3.0, cx=.5, mv='panL', tr='dissolve', fx=['dust'], note='halok qilgani'),
 dict(t=216.80, src='mk:4124', at=2.0, cx=.5, mv='rise', tr='dissolve', note='ustunlikni anglatmaydi'),
 dict(t=223.10, src='mk:3147', at=2.0, cx=.5, mv='pushIn', tr='dissolve', note="javobgarlikdan ozod qilmaydi"),
 # ---------------- ZIYNAT ----------------
 dict(t=227.60, src='mk:100825', at=0.0, cx=.5, mv='rise', tr='dip', sp=0.8, note='yana bir muhim holat'),
 dict(t=231.20, src='mk:2865', at=4.0, cx=.55, mv='pushIn', tr='flash', fx=['gold'], badge=('سورة القصص ٧٩', 'Qasas surasi, 79'), note='ziynatlari bilan chiqdi'),
 dict(t=234.20, src='mk:2861', at=0.5, cx=.5, mv='pullOut', tr='dissolve', fx=['gold', 'rays'], note='ziynat'),
 dict(t=237.40, src='mk:100938', at=0.5, cx=.5, mv='drift', tr='dissolve', note='havas qildilar'),
 dict(t=241.40, src='mk:100941', at=0.0, cx=.5, mv='pushIn', tr='dissolve', note='istaydilar'),
 dict(t=245.30, src='mk:1607', at=1.0, cx=.5, mv='pushIn', tr='dissolve', note='munosabat'),
 dict(t=251.50, src='mk:4240', at=0.5, cx=.5, mv='drift', tr='whip', note='muvaffaqiyat cho\'qqisi'),
 dict(t=254.00, src='mk:42343', at=3.0, cx=.5, mv='panR', tr='dissolve', note='deb hisoblaydi'),
 dict(t=256.60, src='mk:4312', at=0.5, cx=.5, mv='pushIn', tr='dip', fx=['glow'], note='Allohga yaqin qilmaydi'),
 dict(t=262.90, src='wm:mihrimah', at=388.0, cx=.5, mv='rise', tr='dissolve', fx=['rays'], badge=('سورة القصص ٨٠', 'Qasas surasi, 80'), note='ilm berilganlar'),
 dict(t=268.40, src='wm:kaaba_night', at=15.0, cx=.5, mv='pushIn', tr='dissolve', fx=['glow'], note='Allohning savobi yaxshiroq'),
 dict(t=275.40, src='mk:49846', at=4.0, cx=.5, mv='drift', tr='dip', note='ikki qarash'),
 dict(t=278.40, src='mk:18302', at=10.0, cx=.5, mv='pushIn', tr='cut', note='dunyoviy boylik'),
 dict(t=281.50, src='mk:3133', at=1.0, cx=.5, mv='rise', tr='flash', fx=['rays'], note='oxiratdagi mukofot'),
 dict(t=284.70, src='mk:2889', at=6.0, cx=.4, mv='panL', tr='dissolve', note="tashqi ko'rinish"),
 dict(t=289.60, src='mk:28890', at=3.0, cx=.5, mv='pushIn', tr='dissolve', note='sinovga aylangani'),
 # ---------------- YERGA YUTILISH ----------------
 dict(t=294.30, src='mk:4060', at=10.0, cx=.5, mv='pushIn', tr='dip', fx=['lightning'], note='eng muhim voqea'),
 dict(t=297.00, src='img:ms8', mv='pushIn', tr='flash', fx=['glow'], badge=('سورة القصص ٨١', 'Qasas surasi, 81'), note='81-oyat'),
 dict(t=299.60, src='mk:4149', at=5.0, cx=.4, mv='sink', tr='cut', fx=['cracks', 'shake', 'dust'], note='yerga yuttirdi'),
 dict(t=304.00, src='mk:2093', at=6.0, cx=.5, mv='sink', tr='cut', fx=['cracks', 'dust'], note='himoya qiladigan jamoa'),
 dict(t=307.60, src='mk:4423', at=6.0, cx=.4, mv='drift', tr='dissolve', fx=['lightning'], note="o'zini qutqara olmadi"),
 dict(t=311.60, src='img:ms3', mv='panR', tr='dip', fx=['glow'], note='aniq bayon'),
 dict(t=314.60, src='mk:51793', at=1.0, cx=.5, mv='sink', tr='dissolve', note='qaysi shaharda'),
 dict(t=320.40, src='mk:51795', at=1.0, cx=.5, mv='pushIn', tr='dissolve', note='yer ostida saqlangan'),
 dict(t=324.40, src='mk:2092', at=1.0, cx=.5, mv='panL', tr='dissolve', note='dalil yo\'q'),
 dict(t=328.00, src='mk:40746', at=0.5, cx=.5, mv='rise', tr='whip', note='internetda xabarlar'),
 dict(t=334.10, src='mk:2789', at=1.0, cx=.5, mv='pushIn', tr='dissolve', note='arxeologik dalil'),
 dict(t=338.50, src='mk:21612', at=2.5, cx=.6, mv='drift', tr='dissolve', note='xazina joyi emas'),
 dict(t=342.00, src='mk:4148', at=8.0, cx=.5, mv='rise', tr='dissolve', note='asosiy maqsad'),
 dict(t=346.50, src='mk:21585', at=1.0, cx=.5, mv='drift', tr='dissolve', note='kibr oqibati'),
 # ---------------- 82-OYAT ----------------
 dict(t=350.60, src='img:ms7', mv='panL', tr='dip', fx=['glow'], note='yakuniy oyat'),
 dict(t=354.20, src='mk:1944', at=30.0, cx=.5, mv='rise', tr='flash', fx=['rays'], badge=('سورة القصص ٨٢', 'Qasas surasi, 82'), note='fikri o\'zgargan'),
 dict(t=358.20, src='mk:4357', at=0.0, cx=.5, mv='rise', tr='dissolve', sp=0.8, note='rizqni keng qiladi'),
 dict(t=362.00, src='mk:1518', at=0.5, cx=.5, mv='drift', tr='dissolve', note='tor qiladi'),
 dict(t=365.00, src='mk:1191', at=3.0, cx=.5, mv='pushIn', tr='dissolve', note='xohlagan bandalari'),
 dict(t=367.80, src='mk:2093', at=9.0, cx=.5, mv='sink', tr='cut', fx=['cracks', 'shake'], note='bizni ham yuttirgan bo\'lardi'),
 dict(t=370.60, src='mk:4433', at=5.0, cx=.5, mv='pushIn', tr='dip', note='marhamati'),
 dict(t=374.20, src='mk:3458', at=6.0, cx=.5, mv='pushIn', tr='dissolve', note='muhim xulosa'),
 dict(t=377.10, src='mk:4000', at=1.0, cx=.5, mv='drift', tr='dissolve', note='havas qiladi'),
 dict(t=381.00, src='mk:50134', at=2.0, cx=.5, mv='pushIn', tr='dissolve', note='mavqe va imkoniyat'),
 dict(t=385.00, src='mk:28889', at=6.0, cx=.5, mv='pullOut', tr='dip', note="mas'uliyat va sinov"),
 dict(t=390.80, src='mk:4808', at=10.0, cx=.4, mv='drift', tr='dissolve', note='katta farq'),
 # ---------------- BUGUNGI HAYOT ----------------
 dict(t=397.40, src='mk:41375', at=1.0, cx=.5, mv='pushIn', tr='dip', note='bugungi hayotimiz'),
 dict(t=402.90, src='mk:49878', at=8.0, cx=.5, mv='sink', tr='whip', note='muvaffaqiyat mezoni'),
 dict(t=405.50, src='mk:42343', at=12.0, cx=.5, mv='panL', tr='dissolve', note='boylik'),
 dict(t=408.10, src='mk:4196', at=10.0, cx=.5, mv='panR', tr='cut', note='qimmatbaho uylar'),
 dict(t=410.60, src='mk:50134', at=9.0, cx=.5, mv='pushIn', tr='cut', note='avtomobillar'),
 dict(t=413.00, src='mk:2889', at=3.0, cx=.6, mv='pullOut', tr='cut', note='hashamatli hayot'),
 dict(t=415.90, src='wm:kaaba_ramadan', at=63.0, cx=.5, mv='pushIn', tr='flash', fx=['rays'], note='islom ta\'limoti'),
 dict(t=421.00, src='wm:kaaba_ramadan', at=73.0, cx=.5, mv='drift', tr='dissolve', note='taqvo, adolat'),
 dict(t=426.50, src='wm:haram_timelapse', at=100.0, cx=.5, mv='rise', tr='dissolve', note='asosiy saboq'),
 dict(t=431.20, src='mk:4059', at=10.0, cx=.5, mv='pushIn', tr='dissolve', fx=['lightning'], note='hukmidan himoya qilmaydi'),
 dict(t=434.20, src='mk:18296', at=5.0, cx=.5, mv='drift', tr='dissolve', note='shaxsiy qobiliyat'),
 dict(t=437.80, src='mk:1706', at=3.0, cx=.5, mv='rise', tr='dissolve', note='kibrga olib kelishi'),
 # ---------------- BOSHQA OYATLAR ----------------
 dict(t=442.50, src='img:ms6', mv='pushIn', tr='dip', fx=['glow'], note='boshqa oyatlar'),
 dict(t=446.40, src='img:ms4', mv='panL', tr='dissolve', fx=['pattern'], badge=('سورة العنكبوت ٣٩', 'Ankabut surasi, 39'), note='Ankabut 39'),
 dict(t=451.00, src='wm:wadirum', at=10.0, cx=.4, mv='panR', tr='dissolve', fx=['dust'], note="Fir'avn, Homon"),
 dict(t=455.00, src='img:ms3', mv='rise', tr='dissolve', fx=['glow'], badge=('سورة غافر ٢٤', "G'ofir surasi, 24"), note="G'ofir 24"),
 dict(t=458.50, src='mk:4422', at=12.0, cx=.5, mv='drift', tr='dip', fx=['lightning'], note='takabburligi'),
 dict(t=462.50, src='mk:4423', at=8.0, cx=.5, mv='pushIn', tr='dissolve', note='oyatlarga munosabati'),
 dict(t=466.00, src='mk:21585', at=6.0, cx=.5, mv='rise', tr='dissolve', note='faqat mol-dunyo emas'),
 dict(t=470.50, src='mk:40047', at=6.0, cx=.5, mv='drift', tr='dissolve', note="haq yo'ldan yuz o'girish"),
 dict(t=475.00, src='mk:4166', at=3.0, cx=.5, mv='pushIn', tr='dissolve', note='asosiy mavzular'),
 # ---------------- XULOSA ----------------
 dict(t=477.30, src='mk:4148', at=12.0, cx=.5, mv='rise', tr='dip', fx=['pattern'], note='Xulosa'),
 dict(t=481.50, src='mk:4312', at=3.0, cx=.5, mv='pushIn', tr='dissolve', fx=['glow'], note="mas'uliyat"),
 dict(t=485.60, src='mk:2862', at=8.0, cx=.5, mv='pushIn', tr='dissolve', fx=['gold'], note='ulkan xazinalari'),
 dict(t=488.40, src='mk:4149', at=8.0, cx=.55, mv='sink', tr='cut', fx=['cracks', 'shake', 'dust'], note='azobdan saqlay olmadi'),
 dict(t=492.10, src='mk:41375', at=8.0, cx=.5, mv='panL', tr='dip', note="o'zini ustun bilgan"),
 dict(t=496.40, src='mk:2093', at=3.0, cx=.5, mv='sink', tr='dissolve', fx=['cracks'], note='ziyon va halokat'),
 dict(t=500.80, src='mk:18263', at=3.0, cx=.5, mv='pushIn', tr='dip', note="qo'lidagi ne'mat"),
 dict(t=505.00, src='mk:1944', at=40.0, cx=.5, mv='rise', tr='dissolve', fx=['rays'], note='qalbini egallab'),
 dict(t=508.80, src='wm:kaaba_night', at=36.0, cx=.5, mv='pushIn', tr='dissolve', fx=['glow'], note='katta yo\'qotish'),
 dict(t=512.90, src='wm:adhan_vertical', at=20.0, cx=.5, mv='pullOut', tr='flash', fx=['pattern', 'rays'], note='asosiy saboqlar'),
]

# Fallbacks if a Wikimedia download is not available (Wikimedia rate-limits shared IPs)
FALLBACK = {
 'wm:wadirum': ('mk:52012', 2.0), 'wm:wadirum2': ('mk:50199', 3.0), 'wm:ulucami': ('mk:4311', 4.0),
 'wm:bursa_green': ('mk:4312', 1.0), 'wm:crescent_portrait': ('mk:4081', 10.0), 'wm:mecca4k': ('wm:kaaba_ramadan', 45.0),
 'wm:haram_timelapse': ('mk:4312', 2.0), 'wm:mihrimah': ('mk:4311', 2.0), 'wm:kaaba_night': ('mk:4312', 3.0),
 'wm:kaaba_ramadan': ('mk:4311', 6.0), 'wm:adhan_vertical': ('mk:4312', 0.5),
 'img:ms1': 'img:ms7', 'img:ms8': 'img:ms7', 'img:ms2': 'img:ms5',
}

def build():
    shots = []
    for i, s in enumerate(S):
        e = S[i+1]['t'] if i+1 < len(S) else END
        d = dict(id=f's{i:03d}', start=s['t'], end=e, src=s['src'], at=s.get('at', 0.0), cx=s.get('cx', .5),
                 mv=s.get('mv', 'drift'), tr=s.get('tr', 'dissolve'), fx=s.get('fx', []), sp=s.get('sp', 1.0),
                 badge=s.get('badge'), note=s.get('note', ''))
        shots.append(d)
    return shots

if __name__ == '__main__':
    json.dump(dict(duration=END, fps=30, shots=build(), fallback=FALLBACK), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
    print(len(S), 'shots')
