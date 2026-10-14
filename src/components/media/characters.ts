import {COLORS} from '../../lib/theme';

/**
 * Hikoya personajlari — foydalanuvchi AI rasmlaridan kesib olingan avatarlar
 * (public/avatars/*.jpg). Rasm bo'lmasa emoji ishlatiladi.
 */
export const CHARACTERS = {
  fotograf: {src: 'avatars/fotograf.jpg', name: 'Fotograf', emoji: '🤳', color: COLORS.amber},
  yashil: {src: 'avatars/yashil.jpg', name: 'Jasur', emoji: '😩', color: '#84CC16'},
  qizil: {src: 'avatars/qizil.jpg', name: 'Bekzod', emoji: '🥱', color: COLORS.red},
  kok: {src: 'avatars/kok.jpg', name: 'Sardor', emoji: '🤨', color: COLORS.cold},
  ofitsiant: {src: 'avatars/ofitsiant.jpg', name: 'Ofitsiant', emoji: '🧑‍🍳', color: COLORS.green},
} as const;

export type CharacterId = keyof typeof CHARACTERS;
