import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT, FONT, ICE, INK, SERIF } from "../theme";
import { RouteMap } from "./RouteMap";

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

const fadeInOut = (frame: number, dur: number, a = 10, b = 12) =>
  interpolate(frame, [0, a, dur - b, dur], [0, 1, 1, 0], clamp);

const Title: React.FC<{ main: string; sub: string; dur: number }> = ({ main, sub, dur }) => {
  const frame = useCurrentFrame();
  const end = Math.min(dur, 190);
  const o = interpolate(frame, [6, 30, end - 25, end], [0, 1, 1, 0], clamp);
  const ls = interpolate(frame, [0, end], [26, 12], { easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: o }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.15), rgba(0,0,0,0.55) 50%, rgba(0,0,0,0.15))" }} />
      <div style={{ fontFamily: FONT, color: "#fff", fontSize: 118, fontWeight: 900, letterSpacing: ls, textShadow: "0 6px 30px rgba(0,0,0,0.7)" }}>
        {main}
      </div>
      <div style={{ width: interpolate(frame, [20, 60], [0, 820], clamp), height: 3, background: ACCENT, margin: "22px 0" }} />
      <div style={{ fontFamily: FONT, color: ICE, fontSize: 36, fontWeight: 500, letterSpacing: 6, opacity: interpolate(frame, [35, 60], [0, 1], clamp) }}>
        {sub}
      </div>
    </AbsoluteFill>
  );
};

const Chapter: React.FC<{ num: string; title: string; len: number; sceneDur: number }> = ({ num, title, len, sceneDur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = Math.min(Math.round(len * fps), sceneDur);
  if (frame > dur) return null;
  const o = interpolate(frame, [0, 8, dur - 12, dur], [0, 1, 1, 0], clamp);
  const s = spring({ frame, fps, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{ opacity: o, justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "rgba(4,6,10,0.72)" }} />
      <div style={{ fontFamily: SERIF, color: ACCENT, fontSize: 150, fontWeight: 700, opacity: 0.95, transform: `translateY(${(1 - s) * 30}px)` }}>
        {num}
      </div>
      <div style={{ width: 120 * s, height: 3, background: ACCENT, margin: "8px 0 28px" }} />
      <div
        style={{
          fontFamily: FONT, color: "#fff", fontSize: 64, fontWeight: 800, letterSpacing: interpolate(frame, [0, dur], [10, 5]),
          textAlign: "center", maxWidth: 1600, lineHeight: 1.15, transform: `translateY(${(1 - s) * 40}px)`,
        }}
      >
        {title}
      </div>
    </AbsoluteFill>
  );
};

const SubChapter: React.FC<{ text: string; dur: number }> = ({ text, dur }) => {
  const frame = useCurrentFrame();
  const d = Math.min(dur, 130);
  const o = fadeInOut(frame, d, 10, 15);
  return (
    <div style={{ position: "absolute", top: 150, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: o }}>
      <div style={{ fontFamily: FONT, color: "#fff", fontSize: 40, fontWeight: 800, letterSpacing: 6, padding: "12px 30px", background: INK, borderTop: `3px solid ${ACCENT}` }}>
        {text}
      </div>
    </div>
  );
};

const Counter: React.FC<{ c: any; dur: number }> = ({ c, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const o = fadeInOut(frame, dur, 10, 14);
  const p = interpolate(frame, [8, 8 + 1.3 * fps], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const v = Math.round(c.value * p);
  const t2 = c.then ? interpolate(frame, [dur * 0.5, dur * 0.5 + 0.9 * fps], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) }) : 0;
  const fmt = (n: number) => n.toLocaleString("en-US").replace(/,/g, " ");
  return (
    <div style={{ position: "absolute", right: 110, top: 300, opacity: o, fontFamily: FONT, textAlign: "right" }}>
      {c.pre ? <div style={{ color: ACCENT, fontSize: 52, fontWeight: 800, letterSpacing: 4, marginBottom: 6 }}>{c.pre}</div> : null}
      <div style={{ color: "#fff", fontSize: 190, fontWeight: 900, lineHeight: 1, textShadow: "0 8px 30px rgba(0,0,0,0.7)" }}>
        {fmt(v)}
        {c.suffix ? <span style={{ fontSize: 90 }}>{c.suffix}</span> : null}
      </div>
      <div style={{ color: ICE, fontSize: 36, fontWeight: 600, marginTop: 4, textShadow: "0 2px 8px rgba(0,0,0,0.9)" }}>{c.label}</div>
      {c.then ? (
        <div style={{ opacity: t2, marginTop: 26 }}>
          <div style={{ color: ACCENT, fontSize: 120, fontWeight: 900, lineHeight: 1 }}>+{Math.round(c.then.value * t2)}</div>
          <div style={{ color: ICE, fontSize: 32, fontWeight: 600 }}>{c.then.label}</div>
        </div>
      ) : null}
    </div>
  );
};

const Stats: React.FC<{ stats: [number, string][]; dur: number }> = ({ stats, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = Math.round(dur * 0.35);
  const o = interpolate(frame, [start, start + 12, dur - 12, dur], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill style={{ opacity: o, justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "rgba(0,0,0,0.55)" }} />
      <div style={{ display: "flex", gap: 120, fontFamily: FONT }}>
        {stats.map(([n, l], i) => {
          const p = interpolate(frame, [start + i * 10, start + i * 10 + 1.2 * fps], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
          return (
            <div key={i} style={{ textAlign: "center" }}>
              <div style={{ color: i === 1 ? ACCENT : "#fff", fontSize: 200, fontWeight: 900, lineHeight: 1 }}>{Math.round(n * p)}</div>
              <div style={{ color: ICE, fontSize: 40, fontWeight: 600, letterSpacing: 2 }}>{l}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Quote: React.FC<{ text: string; dur: number }> = ({ text, dur }) => {
  const frame = useCurrentFrame();
  const d = Math.min(dur, 150);
  const o = fadeInOut(frame, d, 12, 16);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 380, display: "flex", justifyContent: "center", opacity: o }}>
      <div style={{ fontFamily: SERIF, fontStyle: "italic", color: "#fff", fontSize: 76, textAlign: "center", maxWidth: 1500, padding: "18px 40px", background: "rgba(0,0,0,0.45)", textShadow: "0 4px 20px rgba(0,0,0,0.8)", transform: `scale(${interpolate(frame, [0, d], [0.97, 1.03])})` }}>
        {text}
      </div>
    </div>
  );
};

const Year: React.FC<{ year: string; dur: number }> = ({ year, dur }) => {
  const frame = useCurrentFrame();
  const o = fadeInOut(frame, dur, 8, 10);
  return (
    <div style={{ position: "absolute", right: 100, top: 150, opacity: o, fontFamily: FONT, fontSize: 170, fontWeight: 900, color: "transparent", WebkitTextStroke: `3px ${ACCENT}`, letterSpacing: 6, transform: `translateY(${interpolate(frame, [0, dur], [10, -10])}px)` }}>
      {year}
    </div>
  );
};

const POINT_WORDS = ["", "BIRINCHIDAN", "IKKINCHIDAN", "UCHINCHIDAN", "TO'RTINCHIDAN"];
const Point: React.FC<{ n: number; dur: number }> = ({ n, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 18 } });
  const o = fadeInOut(frame, dur, 6, 12);
  return (
    <div style={{ position: "absolute", left: 96, top: 160, opacity: o, display: "flex", alignItems: "center", gap: 26, fontFamily: FONT }}>
      <div style={{ width: 130, height: 130, borderRadius: 65, border: `4px solid ${ACCENT}`, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 76, fontWeight: 900, transform: `scale(${s})`, background: "rgba(0,0,0,0.45)" }}>
        {n}
      </div>
      <div style={{ color: "#fff", fontSize: 44, fontWeight: 800, letterSpacing: 5, textShadow: "0 2px 10px rgba(0,0,0,0.9)" }}>{POINT_WORDS[n]}</div>
    </div>
  );
};

const InfoList: React.FC<{ items: string[]; dur: number }> = ({ items, dur }) => {
  const frame = useCurrentFrame();
  const o = fadeInOut(frame, dur, 10, 14);
  return (
    <div style={{ position: "absolute", right: 100, top: 260, opacity: o, fontFamily: FONT, background: INK, padding: "30px 40px", borderLeft: `5px solid ${ACCENT}`, minWidth: 600 }}>
      {items.map((it, i) => {
        const p = interpolate(frame, [18 + i * 22, 34 + i * 22], [0, 1], clamp);
        return (
          <div key={i} style={{ opacity: p, transform: `translateX(${(1 - p) * 30}px)`, color: "#fff", fontSize: 38, fontWeight: 600, margin: "12px 0", display: "flex", gap: 18, alignItems: "center" }}>
            <div style={{ width: 14, height: 14, background: ACCENT, transform: "rotate(45deg)" }} />
            {it}
          </div>
        );
      })}
    </div>
  );
};

/** Infographic: how the body uses its reserves in cold + starvation (as narrated). */
const Body: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const o = fadeInOut(frame, dur, 14, 16);
  const stages = [
    ["Tana haroratini saqlash", "qo'shimcha energiya sarfi"],
    ["Energiya zaxiralari", "birinchi navbatda"],
    ["Yog' to'qimalari", "keyin"],
    ["Mushak to'qimalari", "so'ngra"],
    ["Immunitet zaiflashadi", "ichki a'zolar xavf ostida"],
  ];
  const seg = (dur - 60) / stages.length;
  return (
    <AbsoluteFill style={{ opacity: o, justifyContent: "center", alignItems: "flex-end", paddingRight: 110 }}>
      <div style={{ fontFamily: FONT, background: INK, padding: "34px 44px", width: 720, borderLeft: `5px solid ${ACCENT}` }}>
        <div style={{ color: ACCENT, fontSize: 30, fontWeight: 800, letterSpacing: 4, marginBottom: 18 }}>SOVUQ + OCHLIK: ORGANIZM</div>
        {stages.map(([a, b], i) => {
          const p = interpolate(frame, [20 + i * seg, 20 + i * seg + 18], [0, 1], clamp);
          const drain = interpolate(frame, [20 + i * seg, dur], [1, i === 0 ? 0.6 : 0.15], clamp);
          return (
            <div key={i} style={{ opacity: p, margin: "16px 0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", color: "#fff", fontSize: 32, fontWeight: 700 }}>
                <span>{a}</span>
                <span style={{ color: ICE, fontSize: 24, fontWeight: 500 }}>{b}</span>
              </div>
              <div style={{ height: 10, background: "rgba(255,255,255,0.15)", marginTop: 8 }}>
                <div style={{ height: 10, width: `${drain * 100}%`, background: i === 4 ? "#d9534f" : ACCENT }} />
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Timeline of losses exactly as stated in the narration. */
const LossTimeline: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const o = fadeInOut(frame, dur, 10, 14);
  const ev = [
    ["13-oktabr", "halokat", "12"],
    ["keyingi kunlar", "jarohatlar", "5"],
    ["29-oktabr", "qor ko'chkisi", "8"],
    ["noyabr", "", "2"],
    ["11-dekabr", "", "1"],
  ];
  return (
    <AbsoluteFill style={{ opacity: o, justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "rgba(0,0,0,0.6)" }} />
      <div style={{ position: "relative", width: 1600, fontFamily: FONT }}>
        <div style={{ height: 4, background: "rgba(255,255,255,0.3)", width: "100%", position: "absolute", top: 98 }} />
        <div style={{ height: 4, background: ACCENT, width: `${interpolate(frame, [10, dur * 0.7], [0, 100], clamp)}%`, position: "absolute", top: 98 }} />
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          {ev.map(([d, w, n], i) => {
            const p = interpolate(frame, [14 + i * 14, 28 + i * 14], [0, 1], clamp);
            return (
              <div key={i} style={{ width: 260, textAlign: "center", opacity: p }}>
                <div style={{ color: "#fff", fontSize: 64, fontWeight: 900, height: 80 }}>†{n}</div>
                <div style={{ width: 22, height: 22, borderRadius: 11, background: ACCENT, margin: "4px auto 14px" }} />
                <div style={{ color: ICE, fontSize: 30, fontWeight: 700 }}>{d}</div>
                <div style={{ color: "rgba(255,255,255,0.7)", fontSize: 24 }}>{w}</div>
              </div>
            );
          })}
        </div>
        <div style={{ textAlign: "center", marginTop: 60, opacity: interpolate(frame, [dur * 0.55, dur * 0.55 + 15], [0, 1], clamp) }}>
          <span style={{ color: ACCENT, fontSize: 110, fontWeight: 900 }}>16</span>
          <span style={{ color: "#fff", fontSize: 44, fontWeight: 700, marginLeft: 20 }}>kishi tirik qoldi (45 kishidan)</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const EndTitle: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const st = dur - Math.round(6.5 * fps);
  const o = interpolate(frame, [st, st + 20], [0, 1], clamp);
  if (frame < st) return null;
  return (
    <AbsoluteFill style={{ opacity: o, justifyContent: "center", alignItems: "center", background: "rgba(0,0,0,0.78)" }}>
      <div style={{ fontFamily: FONT, color: "#fff", fontSize: 104, fontWeight: 900, letterSpacing: 14 }}>AND TOG'LARI MO'JIZASI</div>
      <div style={{ width: 700, height: 3, background: ACCENT, margin: "26px 0" }} />
      <div style={{ fontFamily: FONT, color: ICE, fontSize: 40, letterSpacing: 6 }}>13.10.1972 — 23.12.1972 • 72 KUN • 45 KISHI • 16 TIRIK</div>
      <div style={{ fontFamily: FONT, color: "rgba(255,255,255,0.55)", fontSize: 22, marginTop: 60, letterSpacing: 2 }}>
        Arxiv materiallari: AP Archive, Archivo DiFilm, TVN Chile, Museo Andes 1972 va boshqalar • to'liq ro'yxat tavsifda
      </div>
    </AbsoluteFill>
  );
};

export const SceneOverlay: React.FC<{ scene: any }> = ({ scene }) => {
  const dur = scene.vTo - scene.vFrom;
  const e = scene.extras || {};
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {e.map ? <RouteMap stage={e.map} dur={dur} /> : null}
      {e.body ? <Body dur={dur} /> : null}
      {e.timeline ? <LossTimeline dur={dur} /> : null}
      {e.stats ? <Stats stats={e.stats} dur={dur} /> : null}
      {e.counter ? <Counter c={e.counter} dur={dur} /> : null}
      {e.info ? <InfoList items={e.info} dur={dur} /> : null}
      {e.quote ? <Quote text={e.quote} dur={dur} /> : null}
      {e.year ? <Year year={e.year} dur={dur} /> : null}
      {e.point ? <Point n={e.point} dur={dur} /> : null}
      {e.sub_chapter ? <SubChapter text={e.sub_chapter} dur={dur} /> : null}
      {e.title ? <Title main={e.title.main} sub={e.title.sub} dur={dur} /> : null}
      {e.chapter ? <Chapter num={e.chapter[0]} title={e.chapter[1]} len={e.chapter_len ?? 3.4} sceneDur={dur} /> : null}
      {e.end_title ? <EndTitle dur={dur} /> : null}
    </AbsoluteFill>
  );
};
