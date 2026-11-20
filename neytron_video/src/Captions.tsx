import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import timeline from './timeline.json';
import {C, HEAD, pop, textStroke} from './theme';

type W = {t: string; s: number; e: number; seg: number};
const words = (timeline as any).words as W[];

// words that get permanent colour emphasis
const KEY = [
  'prezident', 'milliard', 'bank', 'dollar', 'pul', 'hokimiyat', 'algoritm', 'neft', 'gaz', 'elektr', 'energiya',
  'energetika', 'axborot', 'blackrock', 'vanguard', 'state', 'street', 'trillion', 'maxfiy', 'urush', 'aqsh', 'amerika',
  'toshkent', "o'zbekiston", 'federal', 'rezerv', 'bilderberg', 'xitoy', 'rossiya', 'yevropa', 'kuch', 'qudratli',
  'foiz', 'stavka', 'kim', 'yashirin', 'nazorat', 'qaror', 'harbiy', 'yadroviy', 'kongress', 'konstitutsiya',
  'sudlar', 'valyuta', 'kredit', 'investor', 'import', 'texnologi', 'instagram', 'youtube', 'google', 'diqqat',
  'isbot', 'dalil', 'murakkab', 'xato', "noto'g'ri", 'emas', 'savol', 'izoh',
];
const NEG = ['emas', 'xato', "noto'g'ri", 'olmaydi', 'yo\'q', 'isbotlanmagan'];
const norm = (s: string) => s.toLowerCase().replace(/[^a-z'ʻ’0-9-]/g, '');
const isKey = (s: string) => {
  const n = norm(s);
  return KEY.some((k) => n.startsWith(k));
};
const isNeg = (s: string) => NEG.some((k) => norm(s).startsWith(k));

// group into chunks of up to 3 words / ~20 chars, split at punctuation and segment boundaries
type Chunk = {words: W[]; s: number; e: number};
const chunks: Chunk[] = [];
{
  let cur: W[] = [];
  const flush = () => {
    if (cur.length) chunks.push({words: cur, s: cur[0].s, e: cur[cur.length - 1].e});
    cur = [];
  };
  words.forEach((w, i) => {
    const next = words[i + 1];
    cur.push(w);
    const txt = cur.map((x) => x.t).join(' ');
    const punct = /[.,?!:;—]$/.test(w.t);
    if (cur.length >= 4 || txt.length > 26 || punct || !next || next.seg !== w.seg || next.s - w.e > 0.35) flush();
  });
  // extend each chunk until the next one starts (when the gap is short) so captions don't flicker
  chunks.forEach((c, i) => {
    const n = chunks[i + 1];
    if (n && n.s - c.e < 0.6) c.e = n.s;
    else c.e = c.e + 0.25;
  });
}

export const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / 30;
  // binary search current chunk
  let lo = 0, hi = chunks.length - 1, idx = -1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (chunks[m].s <= t) { idx = m; lo = m + 1; } else hi = m - 1;
  }
  if (idx < 0) return null;
  const ch = chunks[idx];
  if (t > ch.e) return null;
  const local = f - Math.round(ch.s * 30);
  const sp = pop(local, 0, 12, 220, 0.6);
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute', top: 850, width: 1600, left: 160, display: 'flex', flexWrap: 'wrap', justifyContent: 'center',
          alignItems: 'center', gap: '6px 18px', transform: `scale(${0.82 + 0.18 * sp}) translateY(${(1 - sp) * 26}px)`,
          opacity: Math.min(1, sp * 1.6),
        }}
      >
        {ch.words.map((w, i) => {
          const nxt = ch.words[i + 1];
          const active = t >= w.s - 0.03 && (!nxt || t < nxt.s - 0.03);
          const said = t >= w.s - 0.03;
          const key = isKey(w.t);
          const neg = isNeg(w.t);
          const aw = pop(f - Math.round(w.s * 30), 0, 10, 260, 0.5);
          const base = neg ? C.red : key ? C.gold : '#fff';
          return (
            <span
              key={i}
              style={{
                position: 'relative', fontFamily: HEAD, fontWeight: 900, fontSize: 70, lineHeight: 1.12,
                textTransform: 'uppercase', letterSpacing: -0.5,
                color: active ? '#0a0a0a' : base,
                opacity: said ? 1 : 0.55,
                transform: `scale(${active ? 1 + 0.08 * aw : 1})`,
                display: 'inline-block', padding: '0 10px',
                textShadow: active ? 'none' : '0 6px 18px rgba(0,0,0,0.85)',
                ...(active ? {} : textStroke(10, '#000')),
              }}
            >
              {active ? (
                <span
                  style={{
                    position: 'absolute', inset: '2px -2px 0 -2px', borderRadius: 14, zIndex: -1,
                    background: neg ? C.red : key ? C.gold : C.green,
                    opacity: Math.min(1, 0.4 + aw), boxShadow: '0 8px 26px rgba(0,0,0,0.5)',
                  }}
                />
              ) : null}
              {w.t.replace(/[,.;:]$/, '')}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
