import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Word} from '../types';
import {sans} from '../fonts';
import {VIDEO} from '../config';

const MAX_WORDS = 8;

// So'zlarni qisqa satrlarga bo'lish (tinish belgilari yoki 8 so'z)
export const chunkWords = (words: Word[]): Word[][] => {
  const chunks: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    cur.push(w);
    const punct = /[.!?:;,—]$/.test(w.t) || /[»"]$/.test(w.t);
    const remaining = words.length - i - 1;
    if ((punct && cur.length >= 3 && remaining !== 1 && remaining !== 2) || cur.length >= MAX_WORDS) {
      chunks.push(cur);
      cur = [];
    }
  });
  if (cur.length) {
    if (cur.length <= 2 && chunks.length) chunks[chunks.length - 1].push(...cur);
    else chunks.push(cur);
  }
  return chunks;
};

// sceneStart: sahna boshlanish vaqti (soniya). Kadr shu sahnaga nisbatan.
export const Captions: React.FC<{words: Word[]; sceneStart: number; sceneEnd: number}> = ({words, sceneStart, sceneEnd}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = sceneStart + frame / fps;
  const chunks = chunkWords(words);
  const idx = chunks.findIndex((c, i) => {
    const next = chunks[i + 1];
    const s = c[0].s;
    const e = next ? next[0].s : sceneEnd + 0.3;
    return t >= s - 0.15 && t < e;
  });
  if (idx < 0) return null;
  const chunk = chunks[idx];
  const cStart = chunk[0].s - 0.15;
  const appear = interpolate(t, [cStart, cStart + 0.25], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <div
      style={{
        position: 'absolute',
        left: 160,
        right: 160,
        bottom: 92,
        textAlign: 'center',
        fontFamily: sans,
        fontWeight: 600,
        fontSize: 50,
        lineHeight: 1.3,
        color: VIDEO.text,
        textShadow: '0 3px 12px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,1)',
        opacity: appear,
        transform: `translateY(${(1 - appear) * 14}px)`,
      }}
    >
      {chunk.map((w, i) => {
        const spoken = t >= w.s;
        const k = interpolate(t, [w.s - 0.05, w.s + 0.2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return (
          <span key={i} style={{color: spoken ? VIDEO.text : 'rgba(244,234,214,0.55)', display: 'inline-block', marginRight: 14}}>
            <span style={{color: k > 0.5 && t < w.s + 0.45 ? VIDEO.accent : undefined}}>{w.t}</span>
          </span>
        );
      })}
    </div>
  );
};
