export type Scene = {
  /** "cross" — to'rt tomonlama chorraha, "T" — uch tomonlama (shimol tarmog'i yo'q), "round" — aylanma */
  layout: "cross" | "T" | "round";
  /** Asosiy yo'l yo'nalishi: "NS" (shimol–janub) yoki "EW" (sharq–g'arb); berilmasa teng ahamiyatli */
  main?: "NS" | "EW";
  /** Tramvay izlari qaysi o'q bo'ylab */
  tram?: "NS" | "EW";
  /** Har bir kirish oldidagi belgi: kirish tomoni → belgi kodi */
  signs?: Partial<Record<Dir, string>>;
  /** Svetofor holati (har bir kirish uchun) */
  lights?: Partial<Record<Dir, "red" | "yellow" | "green" | "green-left" | "off" | "yellow-flash">>;
  vehicles: { id: string; from: Dir; to: Dir; kind?: "car" | "tram" | "ambulance" | "bus" | "truck"; color?: string }[];
  /** Piyodalar: qaysi tarmoqdagi o'tish joyida */
  pedestrians?: Dir[];
  caption?: string;
};

export type Dir = "N" | "S" | "E" | "W";

export type QSeed = {
  /** kategoriya slug */
  c: string;
  /** qiyinlik: E — oson, M — o'rta, H — qiyin */
  d: "E" | "M" | "H";
  q: string;
  o: string[];
  /** to'g'ri javob indeksi (0 dan) */
  a: number;
  /** tushuntirish */
  e: string;
  /** YHQ bandi, masalan "78" yoki "1-ilova, 2.1" */
  r: string;
  /** noto'g'ri variantlar uchun qisqa izohlar: indeks → izoh */
  n?: Record<number, string>;
  sign?: string;
  scene?: Scene;
};
