import {Source} from './types';

/** On-screen attribution labels — one per verified source (see deliverables/Authentic_Media_Sources.csv). */
export const SRC = {
  whDmz: {label: 'The White House (2019) / Wikimedia Commons', license: 'Public domain'},
  whSingapore: {label: 'The White House (2018) / Wikimedia Commons', license: 'Public domain'},
  whHanoi: {label: 'The White House (2019) / Wikimedia Commons', license: 'Public domain'},
  voaSentosa: {label: 'Voice of America (2018) / Wikimedia Commons', license: 'Public domain'},
  voaInterKorean: {label: 'Voice of America (2018) / Wikimedia Commons', license: 'Public domain'},
  kremlinVostochny: {label: 'Kremlin.ru (2023) / Wikimedia Commons', license: 'CC BY 4.0'},
  kremlin2019: {label: 'Kremlin.ru (2019) / Wikimedia Commons', license: 'CC BY 4.0'},
  kremlin2023: {label: 'Kremlin.ru (2023) / Wikimedia Commons', license: 'CC BY 4.0'},
  kremlin2011: {label: 'Kremlin.ru (2011) / Wikimedia Commons', license: 'CC BY 4.0'},
  film1948: {label: 'KXDR Milliy kinostudiyasi, 1948 / Wikimedia Commons', license: 'Public domain'},
  kis1950: {label: 'Arxiv fotosurati, c. 1950 / Wikimedia Commons', license: 'Public domain'},
  ferguson: {label: 'Donny Ferguson (2017) / Wikimedia Commons', license: 'CC BY 3.0'},
  klia2checkin: {label: 'KLIA2, 2016 / Wikimedia Commons', license: 'CC BY-SA 4.0'},
  klia2terminal: {label: 'KLIA2, 2019 / Wikimedia Commons', license: 'CC BY-SA 4.0'},
  klia2aerial: {label: 'KLIA2, 2015 / Wikimedia Commons', license: 'CC BY 2.0'},
  disney: {label: 'Tokyo Disneyland / Wikimedia Commons', license: 'CC BY-SA 3.0'},
  macau: {label: 'Makao, 2013 / Wikimedia Commons', license: 'CC BY-SA 3.0'},
  kumsusan: {label: 'Kumsusan saroyi, Pxenyan / Wikimedia Commons', license: 'CC BY 2.0'},
  opcw: {label: 'OPCW bosh qarorgohi, Gaaga / Wikimedia Commons', license: 'CC BY-SA 4.0'},
  idLetter: {label: 'Indoneziya hukumati maktubi, 2019 / Wikimedia Commons', license: 'Public domain'},
  whPhoto: {label: 'The White House (2018) / Wikimedia Commons', license: 'Public domain'},
} satisfies Record<string, Source>;

export const CREDIT_SOURCES: {name: string; detail: string}[] = [
  {name: 'The White House (Trump Administration archive)', detail: 'Singapur 2018, Xanoy va DMZ 2019 videolari — Public domain'},
  {name: 'Voice of America', detail: 'Sentosa 2018 va Koreyalararo sammit 2018 — Public domain'},
  {name: 'Kremlin.ru', detail: 'Kim Chen Ir (2011), Kim Chen In (2019, 2023) — CC BY 4.0'},
  {name: 'KXDR Milliy kinostudiyasi (1948)', detail: '“South–North Meeting” arxiv filmi — Public domain'},
  {name: 'Donny Ferguson', detail: 'Pxenyan videolari, 2017 — CC BY 3.0'},
  {name: 'Wikimedia Commons mualliflari', detail: 'KLIA2, Tokio, Makao, Pxenyan, Gaaga fotosuratlari — CC BY / CC BY-SA'},
  {name: 'Natural Earth', detail: 'Xarita ma’lumotlari — Public domain'},
  {name: 'Musiqa', detail: 'Ushbu video uchun yaratilgan original sintez partitura'},
];
