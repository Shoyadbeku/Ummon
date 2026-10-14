import {useVideoConfig} from 'remotion';

export type Card = {x: number; y: number; w: number; h: number};

/** Gorizontal (16:9) va vertikal (9:16 Shorts/Reels) uchun rasm kartasi joyi */
export const CARD_H: Card = {x: 310, y: 96, w: 1300, h: 726};
export const CARD_V: Card = {x: 40, y: 250, w: 1000, h: 860};

export const useVertical = () => {
  const {width, height} = useVideoConfig();
  return height > width;
};

export const useCard = (): Card => (useVertical() ? CARD_V : CARD_H);

/** Rasm ichidagi nisbiy nuqta (0..1) → ekran koordinatasi */
export const pointOn = (card: Card, px: number, py: number) => ({x: card.x + px * card.w, y: card.y + py * card.h});
