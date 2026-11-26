import {Source} from './types';

/** On-screen attribution labels — one per verified source (see deliverables/Authentic_Media_Sources.csv). */
export const SRC = {
  whDmz: {label: 'The White House (2019), video kadri / Wikimedia Commons', license: 'Public domain'},
  whSingapore: {label: 'The White House (2018), video kadri / Wikimedia Commons', license: 'Public domain'},
  kremlin2019: {label: 'Kremlin.ru (2019) / Wikimedia Commons', license: 'CC BY 4.0'},
  kremlin2023: {label: 'Kremlin.ru (13.09.2023)', license: 'CC BY 4.0'},
  kremlin2011: {label: 'Kremlin.ru (2011) / Wikimedia Commons', license: 'CC BY 4.0'},
  film1948: {label: 'KXDR Milliy kinostudiyasi, 1948, film kadri / Wikimedia Commons', license: 'Public domain'},
  kis1950: {label: 'Arxiv fotosurati, c. 1950 / Wikimedia Commons', license: 'Public domain'},
  kis1946: {label: 'Arxiv fotosurati, 1946 / Wikimedia Commons', license: 'Public domain'},
  klia2checkin: {label: 'Morio, KLIA2, 2016 / Wikimedia Commons', license: 'CC BY-SA 4.0'},
  klia2terminal: {label: 'Zhou Guanhuai, KLIA2, 2019 / Wikimedia Commons', license: 'CC BY-SA 4.0'},
  klia2aerial: {label: 'Jason Thien, KLIA2, 2015 / Wikimedia Commons', license: 'CC BY 2.0'},
  disney: {label: 'ARICA, Tokyo Disneyland / Wikimedia Commons', license: 'CC BY-SA 3.0'},
  macau: {label: 'Mimihitam, Makao, 2013 / Wikimedia Commons', license: 'CC BY-SA 3.0'},
  kumsusan: {label: 'Mark Scott Johnson, Kumsusan saroyi / Wikimedia Commons', license: 'CC BY 2.0'},
  opcw: {label: 'Steven Lek, OPCW, Gaaga / Wikimedia Commons', license: 'CC BY-SA 4.0'},
  tree: {label: 'Portretlar: Arxiv (PD) · Kremlin.ru (CC BY 4.0) · MBC (CC BY 3.0)', license: 'Wikimedia Commons'},
  idLetter: {label: 'Indoneziya hukumati maktubi, 2019 / Wikimedia Commons', license: 'Public domain'},
} satisfies Record<string, Source>;

export const CREDIT_SOURCES: {name: string; detail: string}[] = [
  {name: 'The White House (Trump Administration)', detail: 'Singapur 2018 va DMZ 2019 videolaridan kadrlar — Public domain'},
  {name: 'Kremlin.ru', detail: 'Kim Chen Ir (2011), Kim Chen In (2019, 2023) — CC BY 4.0'},
  {name: 'KXDR Milliy kinostudiyasi (1948)', detail: '“South–North Meeting” arxiv filmi kadri — Public domain'},
  {name: 'Arxiv fotosuratlari', detail: 'Kim Ir Sen, 1946 va c. 1950 — Public domain'},
  {name: 'Jason Thien · Zhou Guanhuai · Wikimedia Commons', detail: 'KLIA2 fotosuratlari — CC BY 2.0 / CC BY-SA 4.0'},
  {name: 'ARICA · Mimihitam · Mark Scott Johnson', detail: 'Tokio, Makao, Pxenyan — CC BY-SA 3.0 / CC BY 2.0'},
  {name: 'Munhwa Broadcasting Corporation (MBC)', detail: 'Kim Yo Jong portreti (video kadri), 2018 — CC BY 3.0'},
  {name: 'Morio · Steven Lek', detail: 'KLIA2 ro‘yxatdan o‘tish zali, OPCW binosi — CC BY-SA 4.0'},
  {name: 'Indoneziya hukumati', detail: 'Siti Aisyah bo‘yicha maktub, 2019 — Public domain'},
  {name: 'Natural Earth', detail: 'Xarita ma’lumotlari — Public domain'},
  {name: 'Musiqa', detail: 'Ushbu video uchun yaratilgan original sintez partitura'},
];
