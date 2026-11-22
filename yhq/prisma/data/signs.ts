// Yo'l belgilari — YHQ 1-ilovasi (VM 2022-yil 12-apreldagi 172-son qarori) asosida.
// Nomlar rasmiy matndan olingan; "usage" maydonidagi izohlar o'quv maqsadida qisqartirilgan.
export type SignSeed = {
  code: string;
  group: "WARNING" | "PRIORITY" | "PROHIBITORY" | "MANDATORY" | "INFORMATION" | "SERVICE" | "ADDITIONAL";
  name: string;
  meaning: string;
  usage?: string;
  ruleRef?: string;
};

const W = "WARNING" as const;
const P = "PRIORITY" as const;
const X = "PROHIBITORY" as const;
const M = "MANDATORY" as const;
const I = "INFORMATION" as const;
const S = "SERVICE" as const;

const WARN_USAGE =
  "Ogohlantiruvchi belgilar aholi punktlarida xavfli joydan 50–100 metr, aholi punktlaridan tashqarida 150–300 metr oldin o'rnatiladi.";

export const SIGNS: SignSeed[] = [
  // 1. Ogohlantiruvchi belgilar
  { code: "1.1", group: W, name: "Shlagbaumli temir yo'l kesishmasi", meaning: "Oldinda shlagbaum bilan jihozlangan temir yo'l kesishmasi borligini bildiradi.", usage: "Aholi punktlaridan tashqarida takrorlanadi; ikkinchi belgi xavfli joyga kamida 50 m qolganda o'rnatiladi.", ruleRef: "YHQ 1-ilova, 1.1; 18-bob" },
  { code: "1.2", group: W, name: "Shlagbaumsiz temir yo'l kesishmasi", meaning: "Oldinda shlagbaumsiz temir yo'l kesishmasi borligini bildiradi.", usage: "Kesishmadan o'tishdan oldin yaqinlashayotgan poyezd yo'qligiga ishonch hosil qiling.", ruleRef: "YHQ 1-ilova, 1.2; 117-band" },
  { code: "1.3.1", group: W, name: "Bir izli temir yo'l", meaning: "Shlagbaum bilan jihozlanmagan, bir izli temir yo'l kesishmasi.", usage: "Bevosita kesishma oldida, eng yaqin relsdan kamida 20 m masofada o'rnatiladi.", ruleRef: "YHQ 1-ilova, 1.3.1" },
  { code: "1.3.2", group: W, name: "Ko'p izli temir yo'l", meaning: "Shlagbaumsiz, ikki va undan ortiq izli temir yo'l kesishmasi.", usage: "Bevosita kesishma oldida, eng yaqin relsdan kamida 20 m masofada o'rnatiladi.", ruleRef: "YHQ 1-ilova, 1.3.2" },
  { code: "1.5", group: W, name: "Tramvay yo'li bilan kesishuv", meaning: "Oldinda tramvay yo'li bilan kesishuv borligini bildiradi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.5" },
  { code: "1.6", group: W, name: "Teng ahamiyatli yo'llar kesishuvi", meaning: "Oldinda teng ahamiyatli yo'llar chorrahasi. O'ngdan yaqinlashayotgan transportga yo'l beriladi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.6; 105-band" },
  { code: "1.7", group: W, name: "Aylanma harakatlanish bilan kesishuv", meaning: "Oldinda aylanma harakatlanish tashkil etilgan chorraha.", usage: "Aylanada harakatlanayotgan transport aylanaga kirayotganlarga nisbatan imtiyozga ega (98-band).", ruleRef: "YHQ 1-ilova, 1.7; 98-band" },
  { code: "1.8", group: W, name: "Svetofor bilan tartibga solish", meaning: "Harakatlanish svetofor bilan tartibga solinadigan chorraha, piyodalar o'tish joyi yoki yo'l qismini bildiradi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.8" },
  { code: "1.11.1", group: W, name: "Xavfli burilish (o'ngga)", meaning: "Yo'lning kichik radiusli yoki ko'rinishi cheklangan o'ngga burilish joyi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.11.1" },
  { code: "1.11.2", group: W, name: "Xavfli burilish (chapga)", meaning: "Yo'lning kichik radiusli yoki ko'rinishi cheklangan chapga burilish joyi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.11.2" },
  { code: "1.13", group: W, name: "Tik nishablik", meaning: "Oldinda tik nishablik (pastlik) borligini bildiradi.", usage: "Bu belgi bilan belgilangan qismda uzatma yoki ilashish mexanizmi ajratilgan holda harakatlanish taqiqlanadi (130-band).", ruleRef: "YHQ 1-ilova, 1.13; 128–130-bandlar" },
  { code: "1.14", group: W, name: "Tik balandlik", meaning: "Oldinda tik balandlik (ko'tarilish) borligini bildiradi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.14; 128-band" },
  { code: "1.15", group: W, name: "Sirpanchiq yo'l", meaning: "Qatnov qismi o'ta sirpanchiq bo'lgan yo'l qismi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.15" },
  { code: "1.16", group: W, name: "Notekis yo'l", meaning: "Qatnov qismi notekis bo'lgan (o'nqir-cho'nqir, o'ydim-chuqur) yo'l qismi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.16" },
  { code: "1.18.1", group: W, name: "Yo'lning torayishi", meaning: "Yo'lning ikki tomonlama torayishini bildiradi (1.18.2 — o'ngdan, 1.18.3 — chapdan).", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.18.1" },
  { code: "1.19", group: W, name: "Ikki tomonlama harakatlanish", meaning: "Yo'lning (qatnov qismining) qarama-qarshi harakatlanish qismi boshlanishini bildiradi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.19" },
  { code: "1.20", group: W, name: "Piyodalar o'tish joyi", meaning: "5.16.1, 5.16.2 belgilari va (yoki) yo'l chiziqlari bilan belgilangan piyodalar o'tish joyiga yaqinlashayotganingizni bildiradi.", usage: "Tartibga solinmagan o'tish joyida yo'lni kesib o'tayotgan piyodalarni o'tkazib yuborish shart (109-band).", ruleRef: "YHQ 1-ilova, 1.20; 109-band" },
  { code: "1.21", group: W, name: "Bolalar", meaning: "Bolalar muassasasi yaqinidagi yo'l qismida qatnov qismiga bolalar chiqib qolish ehtimolini bildiradi.", usage: "Tegishli belgilar o'rnatilgan maktab va maktabgacha ta'lim tashkilotlari yaqinida (300 m) tezlik 30 km/soat bilan cheklanadi (78-band).", ruleRef: "YHQ 1-ilova, 1.21; 78-band" },
  { code: "1.22", group: W, name: "Velosiped yo'lkasi bilan kesishuv", meaning: "Oldinda velosiped yo'lkasi bilan kesishuv borligini bildiradi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.22" },
  { code: "1.23", group: W, name: "Ta'mirlash ishlari", meaning: "Yo'lda ta'mirlash ishlari olib borilayotganini bildiradi.", usage: "Qisqa muddatli ishlar uchun ish joyidan 10–15 m oldin o'rnatilishi mumkin.", ruleRef: "YHQ 1-ilova, 1.23" },
  { code: "1.24", group: W, name: "Mol haydab o'tish", meaning: "Yo'ldan mol haydab o'tilishi mumkin bo'lgan joy.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.24" },
  { code: "1.25.1", group: W, name: "Yovvoyi hayvonlar", meaning: "Yo'lga yovvoyi hayvonlar chiqib qolishi mumkin bo'lgan joy.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.25.1" },
  { code: "1.26", group: W, name: "Toshlar tushishi", meaning: "Tosh ko'chishi, surilishi va tushishi mumkin bo'lgan yo'l qismi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.26" },
  { code: "1.30", group: W, name: "Boshqa xavf-xatarlar", meaning: "Boshqa ogohlantiruvchi belgilarda ko'zda tutilmagan xavf-xatarlar bo'lgan yo'l qismi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.30" },
  { code: "1.31", group: W, name: "Sun'iy yo'l notekisligi", meaning: "Tezlikni majburiy kamaytirish uchun o'rnatilgan sun'iy notekislikka yaqinlashayotganingizni bildiradi.", usage: WARN_USAGE, ruleRef: "YHQ 1-ilova, 1.31" },

  // 2. Imtiyoz belgilari
  { code: "2.1", group: P, name: "Asosiy yo'l", meaning: "Harakat tartibga solinmagan chorrahalarda oldin o'tish huquqini beradi.", usage: "Asosiy yo'l boshiga va chorrahalarning bevosita oldiga o'rnatiladi. Aholi punktlaridan tashqarida bu belgi bilan belgilangan yo'lning qatnov qismida to'xtab turish taqiqlanadi (92-band).", ruleRef: "YHQ 1-ilova, 2.1; 104-band" },
  { code: "2.2", group: P, name: "Asosiy yo'lning oxiri", meaning: "Asosiy yo'l tugaganini bildiradi.", ruleRef: "YHQ 1-ilova, 2.2" },
  { code: "2.3.1", group: P, name: "Ikkinchi darajali yo'l bilan kesishuv", meaning: "Asosiy yo'lda harakatlanayotganda oldinda ikkinchi darajali yo'l bilan kesishuv borligini bildiradi.", usage: "Aholi punktlarida kesishmagacha 50–100 m, tashqarida 150–300 m masofada o'rnatiladi.", ruleRef: "YHQ 1-ilova, 2.3.1" },
  { code: "2.4", group: P, name: "Yo'l bering!", meaning: "Haydovchi kesib o'tilayotgan yo'ldan (7.13 belgisi bo'lsa — asosiy yo'ldan) harakatlanayotgan transport vositasiga yo'l berishi kerak.", ruleRef: "YHQ 1-ilova, 2.4" },
  { code: "2.5", group: P, name: "To'xtamasdan harakatlanish taqiqlangan", meaning: "To'xtash chizig'i oldida, u bo'lmasa kesib o'tiladigan qatnov qismining chetida to'xtamasdan harakatlanish taqiqlanadi va kesib o'tilayotgan yo'ldagi transportga yo'l beriladi.", usage: "Temir yo'l kesishmasi yoki karantin maskanidan oldin ham o'rnatilishi mumkin.", ruleRef: "YHQ 1-ilova, 2.5" },
  { code: "2.6", group: P, name: "Ro'para harakatlanishning ustunligi", meaning: "Qarama-qarshi harakatni qiyinlashtiradigan bo'lsa, yo'lning tor qismiga kirish taqiqlanadi; haydovchi tor qismdagi yoki ro'paradan unga yaqin bo'lgan transportga yo'l berishi kerak.", ruleRef: "YHQ 1-ilova, 2.6" },
  { code: "2.7", group: P, name: "Ro'paradagi harakatlanishga nisbatan imtiyoz", meaning: "Yo'lning tor qismida haydovchi ro'paradan kelayotgan transport vositasiga nisbatan imtiyozga ega ekanini bildiradi.", ruleRef: "YHQ 1-ilova, 2.7" },

  // 3. Taqiqlovchi belgilar
  { code: "3.1", group: X, name: "Kirish taqiqlangan", meaning: "Barcha transport vositalarining kirishi taqiqlanishini bildiradi.", usage: "Yo'nalishli transport vositalariga taalluqli emas.", ruleRef: "YHQ 1-ilova, 3.1" },
  { code: "3.2", group: X, name: "Harakatlanish taqiqlangan", meaning: "Barcha transport vositalarining harakatlanishi taqiqlanishini bildiradi.", usage: "Belgi ta'sir oralig'idagi korxonalarga xizmat ko'rsatuvchi, u yerda yashovchi yoki ishlovchi fuqarolarga tegishli transportga ta'sir qilmaydi.", ruleRef: "YHQ 1-ilova, 3.2" },
  { code: "3.3", group: X, name: "Mexanik transport vositalarining harakatlanishi taqiqlangan", meaning: "Mexanik transport vositalarining harakatlanishi taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.3" },
  { code: "3.4", group: X, name: "Yuk avtomobillarining harakatlanishi taqiqlangan", meaning: "Ruxsat etilgan to'liq vazni 3,5 tonnadan (yoki belgida ko'rsatilgandan) ortiq yuk avtomobillari, traktorlar va o'ziyurar uskunalarning harakatlanishi taqiqlanadi.", usage: "Odam tashish uchun mo'ljallangan yuk avtomobillarining harakatlanishini taqiqlamaydi.", ruleRef: "YHQ 1-ilova, 3.4" },
  { code: "3.9", group: X, name: "Velosipedda harakatlanish taqiqlangan", meaning: "Velosipedda va mopedda harakatlanish taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.9" },
  { code: "3.10", group: X, name: "Piyodaning harakatlanishi taqiqlangan", meaning: "Piyodalarning harakatlanishi taqiqlanadi.", usage: "Belgi yo'lning qaysi tomonida o'rnatilgan bo'lsa, faqat o'sha tomonga amal qiladi.", ruleRef: "YHQ 1-ilova, 3.10" },
  { code: "3.13", group: X, name: "Cheklangan balandlik", meaning: "Gabarit balandligi (yuk bilan yoki yuksiz) belgida ko'rsatilgandan ortiq transport vositalarining harakatlanishi taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.13" },
  { code: "3.18.1", group: X, name: "O'ngga burilish taqiqlangan", meaning: "Qaysi kesishma oldiga o'rnatilgan bo'lsa, shu kesishmada o'ngga burilish taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.18.1" },
  { code: "3.18.2", group: X, name: "Chapga burilish taqiqlanadi", meaning: "Qaysi kesishma oldiga o'rnatilgan bo'lsa, shu kesishmada chapga burilish taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.18.2" },
  { code: "3.19", group: X, name: "Qayrilish taqiqlangan", meaning: "Qayrilib olish taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.19" },
  { code: "3.20", group: X, name: "Quvib o'tish taqiqlangan", meaning: "Soatiga 40 km dan kam tezlikda harakatlanayotgan yakka transport vositasidan boshqa transport vositalarini quvib o'tish taqiqlanadi.", usage: "Ta'siri belgi o'rnatilgan joydan eng yaqin chorrahagacha, u bo'lmasa aholi punktining oxirigacha davom etadi.", ruleRef: "YHQ 1-ilova, 3.20; 86-band" },
  { code: "3.21", group: X, name: "Quvib o'tish taqiqlangan hududning oxiri", meaning: "3.20 belgisi ta'sir hududining oxiri.", ruleRef: "YHQ 1-ilova, 3.21" },
  { code: "3.22", group: X, name: "Yuk avtomobillarida quvib o'tish taqiqlangan", meaning: "To'liq vazni 3,5 tonnadan ortiq yuk avtomobillarida barcha transport vositalarini quvib o'tish taqiqlanadi (40 km/soatdan sekin harakatlanayotgan transport, traktor, ot-arava, velosiped bundan mustasno).", ruleRef: "YHQ 1-ilova, 3.22" },
  { code: "3.24", group: X, name: "Yuqori tezlik cheklangan", meaning: "Belgida ko'rsatilganidan ortiq tezlikda (km/soat) harakatlanish taqiqlanadi.", usage: "Aholi punktiga yetmasdan o'rnatilgan 3.24 belgisining ta'siri 5.22 belgisigacha saqlanadi.", ruleRef: "YHQ 1-ilova, 3.24" },
  { code: "3.25", group: X, name: "Yuqori tezlik cheklangan hududning oxiri", meaning: "3.24 belgisi ta'sir hududining oxiri.", ruleRef: "YHQ 1-ilova, 3.25" },
  { code: "3.26", group: X, name: "Tovush moslamalaridan foydalanish taqiqlangan", meaning: "Yo'l-transport hodisasining oldini olish hollaridan boshqa vaziyatlarda tovush moslamasidan foydalanish taqiqlanadi.", ruleRef: "YHQ 1-ilova, 3.26" },
  { code: "3.27", group: X, name: "To'xtash taqiqlangan", meaning: "Transport vositalarining to'xtashi va to'xtab turishi taqiqlanadi.", usage: "Belgi yo'lning qaysi tomonida o'rnatilgan bo'lsa, o'sha tomonga amal qiladi. Yo'nalishsiz yengil taksilarga yo'lovchini tushirish-chiqarish vaqtida ta'sir qilmaydi.", ruleRef: "YHQ 1-ilova, 3.27" },
  { code: "3.28", group: X, name: "To'xtab turish taqiqlangan", meaning: "Transport vositalarining to'xtab turishi taqiqlanadi (to'xtashga ruxsat etiladi).", usage: "Taksometri ishlab turgan taksilarga taalluqli emas.", ruleRef: "YHQ 1-ilova, 3.28" },
  { code: "3.31", group: X, name: "Barcha cheklovlarning oxiri", meaning: "3.16, 3.20, 3.22, 3.24, 3.26–3.30 belgilaridan bir nechtasi bir vaqtda amal qiladigan hududning oxiri.", ruleRef: "YHQ 1-ilova, 3.31" },

  // 4. Buyuruvchi belgilar
  { code: "4.1.1", group: M, name: "Harakatlanish to'g'riga", meaning: "Faqat to'g'riga harakatlanishga ruxsat etiladi.", usage: "Yo'l qismi boshida o'rnatilgan bo'lsa, ta'siri yaqin chorrahagacha; o'ngdagi hovlilarga burilishni taqiqlamaydi.", ruleRef: "YHQ 1-ilova, 4.1.1" },
  { code: "4.1.2", group: M, name: "Harakatlanish o'ngga", meaning: "Faqat o'ngga harakatlanishga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.1.2" },
  { code: "4.1.3", group: M, name: "Harakatlanish chapga", meaning: "Faqat chapga harakatlanishga ruxsat etiladi. Chapga burilishga ruxsat beruvchi belgi qayrilib olishga ham ruxsat beradi.", ruleRef: "YHQ 1-ilova, 4.1.3" },
  { code: "4.1.4", group: M, name: "Harakatlanish to'g'riga yoki o'ngga", meaning: "Faqat to'g'riga yoki o'ngga harakatlanishga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.1.4" },
  { code: "4.2.1", group: M, name: "To'siqni chapdan aylanib o'tish", meaning: "Faqat ko'rsatkich ko'rsatgan (chap) tomondan aylanib o'tishga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.2.1" },
  { code: "4.2.2", group: M, name: "To'siqni o'ngdan aylanib o'tish", meaning: "Faqat ko'rsatkich ko'rsatgan (o'ng) tomondan aylanib o'tishga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.2.2" },
  { code: "4.3", group: M, name: "Aylanma harakatlanish", meaning: "Ko'rsatkichlar yo'nalishida (aylana bo'ylab) harakatlanishga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.3" },
  { code: "4.5", group: M, name: "Velosiped yo'lkasi", meaning: "Faqat velosiped va individual harakatlanish vositalarida harakatlanishga ruxsat etiladi. Trotuar bo'lmasa, piyodalar ham yurishi mumkin.", ruleRef: "YHQ 1-ilova, 4.5" },
  { code: "4.6", group: M, name: "Piyodalar yo'lkasi", meaning: "Faqat piyodalar yurishiga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.6" },
  { code: "4.7", group: M, name: "Eng kam tezlik", meaning: "Faqat belgida ko'rsatilgan yoki undan yuqori tezlikda harakatlanishga ruxsat etiladi.", ruleRef: "YHQ 1-ilova, 4.7" },

  // 5. Axborot-ko'rsatgich belgilari
  { code: "5.1", group: I, name: "Avtomagistral", meaning: "YHQning avtomagistrallarda harakatlanish tartibi o'rnatilgan yo'lni bildiradi.", usage: "Avtomagistralda piyodalar, velosiped, moped, traktor va tezligi 40 km/soatdan kam transportning harakatlanishi, orqaga yurish va qayrilib olish taqiqlanadi (121-band).", ruleRef: "YHQ 1-ilova, 5.1; 121-band" },
  { code: "5.5", group: I, name: "Bir tomonlama harakatli yo'l", meaning: "Transport vositalari butun kenglik bo'yicha bir yo'nalishda harakatlanadigan yo'l yoki qatnov qismi.", ruleRef: "YHQ 1-ilova, 5.5" },
  { code: "5.9", group: I, name: "Yo'nalishli transport vositalari uchun mo'ljallangan tasma", meaning: "Yo'nalishli transport vositalari uchun ajratilgan tasmani bildiradi; boshqa transportning bu tasmada harakatlanishi va to'xtashi taqiqlanadi.", ruleRef: "YHQ 1-ilova, 5.9; 132-band" },
  { code: "5.12", group: I, name: "Avtobus va (yoki) trolleybus to'xtash joyi", meaning: "Avtobus va (yoki) trolleybus bekatini bildiradi.", ruleRef: "YHQ 1-ilova, 5.12" },
  { code: "5.15", group: I, name: "To'xtab turish joyi", meaning: "To'xtab turish (avtoturargoh) joyini bildiradi.", ruleRef: "YHQ 1-ilova, 5.15" },
  { code: "5.16.1", group: I, name: "Piyodalar o'tish joyi", meaning: "Piyodalar o'tish joyini bildiradi.", ruleRef: "YHQ 1-ilova, 5.16.1" },
  { code: "5.22", group: I, name: "Aholi punktining boshlanishi", meaning: "YHQning aholi punktlarida harakatlanish tartibi talablariga amal qilinadigan joyning nomi va boshlanishini bildiradi.", usage: "Shu belgidan boshlab aholi punktlari uchun belgilangan tezlik cheklovlari amal qiladi (78-band).", ruleRef: "YHQ 1-ilova, 5.22; 78-band" },
  { code: "5.23", group: I, name: "Aholi punktining oxiri", meaning: "Aholi punktlarida harakatlanish tartib-talablari bekor qilingan joyni bildiradi.", ruleRef: "YHQ 1-ilova, 5.23" },
  { code: "5.33", group: I, name: "To'xtash chizig'i", meaning: "Svetoforning (tartibga soluvchining) taqiqlovchi ishorasida transport vositalari to'xtaydigan joyni bildiradi.", ruleRef: "YHQ 1-ilova, 5.33; 41-band" },
  { code: "5.38", group: I, name: "Turar joy dahasi", meaning: "YHQning turar joy dahalarida harakatlanish tartibi o'rnatilgan hududni bildiradi.", usage: "Turar joy dahasida tezlik 20 km/soatdan oshmasligi kerak; piyodalar qatnov qismida ham yurishi mumkin va imtiyozga ega (78, 123-bandlar).", ruleRef: "YHQ 1-ilova, 5.38; 20-bob" },
  { code: "5.39", group: I, name: "Turar joy dahasining oxiri", meaning: "Turar joy dahasi tugaganini bildiradi. Undan chiqishda boshqa harakat ishtirokchilariga yo'l beriladi (126-band).", ruleRef: "YHQ 1-ilova, 5.39; 126-band" },

  // 6. Servis belgilari
  { code: "6.1", group: S, name: "Tibbiy yordam ko'rsatish joyi", meaning: "Tibbiy yordam ko'rsatish joyini bildiradi.", ruleRef: "YHQ 1-ilova, 6.1" },
  { code: "6.3.1", group: S, name: "Avtomobillarga yonilg'i quyish shoxobchasi", meaning: "Yonilg'i quyish shoxobchasini bildiradi.", ruleRef: "YHQ 1-ilova, 6.3.1" },
  { code: "6.11", group: S, name: "Dam olish joyi", meaning: "Dam olish joyini bildiradi.", usage: "Avtomagistralda to'xtashga faqat 5.15 yoki 6.11 belgilari bilan belgilangan maydonchalarda ruxsat etiladi (121-band).", ruleRef: "YHQ 1-ilova, 6.11; 121-band" },
];
