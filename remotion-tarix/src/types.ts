export type Word = {t: string; s: number}; // so'z va boshlanish vaqti (soniya, ovozga nisbatan)
export type SceneData = {
  n: number; // rasm raqami (01..60)
  repeat: boolean; // rasm qayta ishlatilganmi
  image: string; // public/ ichidagi yo'l
  text: string; // ekranda chiqadigan matn
  start: number; // soniya (ovoz boshidan)
  end: number;
  words: Word[];
};
