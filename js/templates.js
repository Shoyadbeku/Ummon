// Subtitr uslublari va video shablonlari.
// anim: none | karaoke (aytilgan so‘zlar bo‘yaladi) | pop (faol so‘z kattalashadi) |
//       highlight (faol so‘z orqasida quti) | typewriter (so‘zlar birin-ketin) | bounce | fade

export const CAPTION_STYLES = [
  { id: 'karaoke', name: 'Karaoke', font: 'Montserrat', weight: 900, size: 0.075, color: '#ffffff', active: '#ffd43b',
    stroke: 0.14, strokeColor: '#000000', upper: false, anim: 'karaoke', maxWords: 4 },
  { id: 'pop', name: 'Pop', font: 'Montserrat', weight: 900, size: 0.085, color: '#ffffff', active: '#7cff4f',
    stroke: 0.16, strokeColor: '#000000', upper: true, anim: 'pop', maxWords: 3 },
  { id: 'highlight', name: 'Belgilash', font: 'Montserrat', weight: 800, size: 0.07, color: '#ffffff', active: '#ffffff',
    activeBg: '#6e5bff', stroke: 0.12, strokeColor: '#000000', upper: false, anim: 'highlight', maxWords: 4 },
  { id: 'classic', name: 'Klassik', font: 'Manrope', weight: 800, size: 0.058, color: '#ffffff', active: '#ffffff',
    stroke: 0.12, strokeColor: '#000000', upper: false, anim: 'none', maxWords: 0 },
  { id: 'box', name: 'Qutichali', font: 'Manrope', weight: 800, size: 0.056, color: '#ffffff', active: '#ffffff',
    box: true, boxColor: 'rgba(0,0,0,0.72)', upper: false, anim: 'fade', maxWords: 0 },
  { id: 'headline', name: 'Sarlavha', font: 'Bebas Neue', weight: 400, size: 0.13, color: '#ffd43b', active: '#ffffff',
    stroke: 0.06, strokeColor: '#000000', shadow: 18, shadowColor: 'rgba(0,0,0,0.6)', upper: true, anim: 'bounce', maxWords: 2 },
  { id: 'neon', name: 'Neon', font: 'Unbounded', weight: 700, size: 0.062, color: '#c9fbff', active: '#00f0ff',
    shadow: 22, shadowColor: '#00e5ff', upper: false, anim: 'karaoke', maxWords: 3 },
  { id: 'typewriter', name: 'Mashinka', font: 'Unbounded', weight: 500, size: 0.052, color: '#ffffff', active: '#ffb23f',
    box: true, boxColor: 'rgba(19,17,27,0.85)', upper: false, anim: 'typewriter', maxWords: 0 },
  { id: 'minimal', name: 'Minimal', font: 'Manrope', weight: 600, size: 0.044, color: '#ffffff', active: '#ffffff',
    shadow: 8, shadowColor: 'rgba(0,0,0,0.9)', upper: false, anim: 'none', maxWords: 0, pos: 0.86 },
  { id: 'cinema', name: 'Kino', font: 'Playfair Display', weight: 700, italic: true, size: 0.058, color: '#fff4dc', active: '#fff4dc',
    shadow: 10, shadowColor: 'rgba(0,0,0,0.9)', upper: false, anim: 'fade', maxWords: 0, pos: 0.84 },
  { id: 'handwritten', name: 'Qo‘lyozma', font: 'Caveat', weight: 700, size: 0.1, color: '#ffffff', active: '#ffb3d9',
    stroke: 0.08, strokeColor: 'rgba(0,0,0,0.6)', upper: false, anim: 'karaoke', maxWords: 3 },
  { id: 'bold-box', name: 'Lenta', font: 'Montserrat', weight: 900, size: 0.07, color: '#13111b', active: '#13111b',
    box: true, boxColor: '#ffb23f', perLineBox: true, upper: true, anim: 'bounce', maxWords: 3 },
];

export const VIDEO_TEMPLATES = [
  { id: 'reels', name: 'Reels hook', desc: '9:16 · katta so‘zlar', aspect: '9:16', fit: 'cover', style: 'pop',
    hook: 'Buni bilmasangiz, vaqt yo‘qotasiz', hookStyle: 'pill', bg: 0 },
  { id: 'shorts', name: 'YouTube Shorts', desc: '9:16 · karaoke', aspect: '9:16', fit: 'cover', style: 'karaoke',
    hook: '', hookStyle: 'pill', bg: 1 },
  { id: 'podcast', name: 'Podkast klip', desc: '16:9 videodan vertikal', aspect: '9:16', fit: 'contain', bgMode: 'blur', style: 'box',
    hook: 'Podkast · 12-son', hookStyle: 'accent', bg: 2 },
  { id: 'post', name: 'Instagram post', desc: '1:1 · klassik', aspect: '1:1', fit: 'cover', style: 'highlight',
    hook: '', hookStyle: 'pill', bg: 3 },
  { id: 'lesson', name: 'Dars', desc: '16:9 · minimal', aspect: '16:9', fit: 'contain', bgMode: 'color', style: 'minimal',
    hook: '3-dars: Excel asoslari', hookStyle: 'outline', bg: 4 },
  { id: 'promo', name: 'Mahsulot reklamasi', desc: '9:16 · sarlavha', aspect: '9:16', fit: 'cover', style: 'headline',
    hook: 'Yangi kolleksiya · 30% chegirma', hookStyle: 'accent', bg: 5 },
  { id: 'cinema', name: 'Kino iqtibos', desc: '16:9 · serif', aspect: '16:9', fit: 'cover', style: 'cinema',
    hook: '', hookStyle: 'outline', bg: 6 },
  { id: 'vlog', name: 'Vlog', desc: '4:5 · qo‘lyozma', aspect: '4:5', fit: 'cover', style: 'handwritten',
    hook: 'Toshkentda bir kun', hookStyle: 'outline', bg: 7 },
];

// Video bo‘lmaganda ishlatiladigan fonlar (ikki rangli gradient)
export const BACKGROUNDS = [
  ['#2b1f6b', '#ff7a59'], ['#0f3443', '#34e89e'], ['#1d1a2f', '#6e5bff'], ['#4a1942', '#ffb23f'],
  ['#0b132b', '#3a506b'], ['#141e30', '#ff4e7a'], ['#1b1b1b', '#5a4632'], ['#355c7d', '#f8b195'],
  ['#000000', '#222222'], ['#f7f3e8', '#e3d5b8'], ['#003049', '#d62828'], ['#283618', '#dda15e'],
];

export const DEMO_SEGMENTS = [
  { start: 0.2, end: 2.6, text: 'Assalomu alaykum, do‘stlar!' },
  { start: 2.6, end: 5.6, text: 'Bugun videoga o‘zbekcha subtitr qo‘shamiz' },
  { start: 5.6, end: 8.6, text: 'Shablonni tanlang va bir bosishda yuklab oling' },
];

export function styleById(id) {
  return CAPTION_STYLES.find((s) => s.id === id) || CAPTION_STYLES[0];
}
