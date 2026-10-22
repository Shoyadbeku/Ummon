import {spring, useCurrentFrame, useVideoConfig} from 'remotion';

type Word = {text: string; start: number; end: number};
type Chunk = {words: Word[]; start: number; end: number};

// Gap ichida so'zlar vaqti harflar soniga qarab taqsimlanadi.
const toWords = (line: {start: number; end: number; text: string}): Word[] => {
  const parts = line.text.split(/\s+/).filter(Boolean);
  const weights = parts.map((p) => p.replace(/[^\p{L}\d]/gu, '').length + 1.5);
  const total = weights.reduce((a, b) => a + b, 0);
  let t = line.start;
  return parts.map((text, i) => {
    const d = ((line.end - line.start) * weights[i]) / total;
    const w = {text, start: t, end: t + d};
    t += d;
    return w;
  });
};

const toChunks = (lines: {start: number; end: number; text: string}[]): Chunk[] => {
  const chunks: Chunk[] = [];
  lines.forEach((line, li) => {
    const words = toWords(line);
    let cur: Word[] = [];
    const flush = () => {
      if (cur.length) chunks.push({words: cur, start: cur[0].start, end: cur[cur.length - 1].end});
      cur = [];
    };
    words.forEach((w) => {
      const len = cur.map((c) => c.text).join(' ').length + w.text.length;
      if (cur.length >= 3 || len > 20) flush();
      cur.push(w);
      if (/[!?,.—]$/.test(w.text) && cur.length >= 2) flush();
    });
    flush();
    // Gap oxiridagi bo'lak keyingi gapgacha (ko'pi bilan 0.5 s) ekranda qoladi.
    const last = chunks[chunks.length - 1];
    const next = lines[li + 1]?.start ?? line.end + 0.6;
    last.end = Math.min(next, line.end + 0.5);
  });
  for (let i = 0; i < chunks.length - 1; i++) {
    chunks[i].end = Math.min(Math.max(chunks[i].end, chunks[i + 1].start), chunks[i + 1].start);
  }
  return chunks;
};

export const Subtitles: React.FC<{lines: {start: number; end: number; text: string}[]; hideAfter: number}> = ({
  lines,
  hideAfter,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  if (t >= hideAfter) return null;
  const chunk = toChunks(lines).find((c) => t >= c.start && t < c.end);
  if (!chunk) return null;

  const enter = spring({frame: frame - Math.round(chunk.start * fps), fps, config: {damping: 12, stiffness: 220}});

  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        top: 1280,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: '0 40px',
        transform: `translateY(${(1 - enter) * 40}px) scale(${0.85 + enter * 0.15})`,
        opacity: Math.min(1, enter * 1.5),
      }}
    >
      {chunk.words.map((w, i) => {
        const active = t >= w.start && t < w.end + 0.05;
        const said = t >= w.start;
        const pop = spring({frame: frame - Math.round(w.start * fps), fps, config: {damping: 10, stiffness: 300}});
        return (
          <span
            key={i}
            style={{
              fontSize: 92,
              fontWeight: 900,
              lineHeight: 1.12,
              letterSpacing: -1,
              textTransform: 'uppercase',
              color: active ? '#FFD84D' : said ? '#ffffff' : 'rgba(255,255,255,0.75)',
              WebkitTextStroke: '14px #0b0b10',
              paintOrder: 'stroke fill',
              textShadow: '0 10px 28px rgba(0,0,0,0.6)',
              display: 'inline-block',
              transform: `scale(${active ? 1 + 0.12 * pop : 1}) rotate(${active ? -2 : 0}deg)`,
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
