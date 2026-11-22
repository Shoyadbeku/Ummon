import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Shot, ShotProps} from './components/Shot';
import {Kinetic, Counter, YearStamp, Chapter, Callout, Quote} from './components/Graphics';
import {MapScene} from './components/MapScene';
import {PixelCity, LogoCard, Split, IconGrid, TimedList, Panels, HackUI, TrailerUI, DateShift, Platforms, TimelineRecap, Poll, BigWord} from './components/Scenes';

// ---------------------------------------------------------------------
// Storyboard. Every scene starts at `t` (seconds, synced to the voice)
// and lasts until the next scene starts. `fg` items are overlays; `at` is
// seconds relative to the scene start. `fx` = entrance transition.
// `sfx` = sound cues (parsed by scripts/mix.py — keep one scene per line).
// ---------------------------------------------------------------------

export type Fx = 'cut' | 'zoom' | 'flash' | 'glitch' | 'shake' | 'whip' | 'leak' | 'blur';
export type Fg = {at?: number; until?: number; el: (dur: number) => React.ReactNode};
export type Scene = {t: number; bg: (dur: number) => React.ReactNode; fg?: Fg[]; fx?: Fx; sfx?: string[]; chapter?: string};

const v = (src: string, o: Partial<ShotProps> = {}): ShotProps => ({src: `media/${src}.mp4`, kind: 'video', ...o});
const im = (src: string, o: Partial<ShotProps> = {}): ShotProps => ({src: `img/${src}`, kind: 'image', ...o});
const B = (p: ShotProps) => (dur: number) => <Shot {...p} dur={dur} />;
const dark = (c = '#06060a') => () => <AbsoluteFill style={{background: `radial-gradient(circle at 50% 35%, #1a1a2a 0%, ${c} 70%)`}} />;
const K = (lines: string[], o: {color?: string; size?: number; top?: number; at?: number; until?: number} = {}): Fg => ({at: o.at, until: o.until, el: (d) => <Kinetic lines={lines} color={o.color} size={o.size} top={o.top} dur={d} />});
const CO = (title: string, sub?: string, o: {color?: string; top?: number; at?: number; until?: number} = {}): Fg => ({at: o.at, until: o.until, el: () => <Callout title={title} sub={sub} color={o.color} top={o.top} />});

export const SCENES: Scene[] = [
  // ============================ HOOK ============================
  {t: 0.0, bg: B(v('vhs_sun_palms', {kb: 'in', grade: 'night'})), fg: [K(['*GTA*', 'TARIXI'], {size: 230, top: 330})], fx: 'flash', sfx: ['impact_big', 'whoosh1']},
  {t: 1.55, bg: B(v('aerial_city_night', {kb: 'in', from: 2})), fg: [K(['ODDIY', '*O‘YINDAN*'], {size: 170})], fx: 'whip', sfx: ['whoosh2']},
  {t: 2.85, bg: B(v('banknotes_falling', {kb: 'out', grade: 'warm'})), fg: [K(['*MILLIARD $*', 'IMPERIYAGACHA'], {size: 150})], fx: 'flash', sfx: ['impact_zoom', 'coin']},
  {t: 5.1, bg: () => <LogoCard src="img/logo_gta6.png" color="pink" dur={60} />, fx: 'glitch', sfx: ['bass_hit', 'glitch1']},
  {t: 6.9, bg: B(v('police_lights2', {kb: 'in'})), fg: [K(['DUNYO', '*HAYRATDA*'], {size: 170, color: 'cyan'})], fx: 'zoom', sfx: ['whoosh3']},
  {t: 8.7, bg: B(v('vhs_eject', {kb: 'in', dim: 0.35, grade: 'warm'})), fg: [{at: 0.4, el: () => <YearStamp year={1997} label="Tasavvur qiling" prev={2026} />}], fx: 'blur', sfx: ['riser_short', 'type_click']},
  {t: 11.9, bg: () => <PixelCity mode="top" />, fg: [CO('Yuqoridan ko‘rinish', 'oddiy bir o‘yin', {top: 230, until: 3.7}), CO('Sodda grafika', 'kichkina mashinalar', {top: 230, at: 3.8, color: 'cyan'})], fx: 'glitch', sfx: ['glitch2', 'pixel_boom']},
  {t: 20.2, bg: B(v('programmer_hands', {fit: 'card', kb: 'in'})), fg: [CO('Dasturchilar', 'o‘sha paytda...', {top: 260})], fx: 'whip', sfx: ['whoosh4', 'typing']},
  {t: 22.8, bg: B(v('dev_screen', {kb: 'right', grade: 'teal'})), fg: [], fx: 'zoom', sfx: ['sweep1']},
  {t: 24.6, bg: B(v('crowd_arms', {kb: 'in'})), fg: [K(['O‘YIN *SANOATINI*', 'O‘ZGARTIRADI'], {size: 120})], fx: 'flash', sfx: ['whoosh1']},
  {t: 28.4, bg: B(v('hourglass_finish', {kb: 'in', dim: 0.3})), fg: [{el: () => <Counter to={30} suffix=" YIL" label="Oradan qariyb" countDur={36} />}], fx: 'zoom', sfx: ['riser_short', 'ding']},
  {t: 31.0, bg: B(v('crowd_junction', {kb: 'in'})), fg: [K(['BUTUN DUNYO', '*BITTA* O‘YINNI', 'KUTMOQDA'], {size: 120})], fx: 'whip', sfx: ['whoosh2']},
  {t: 33.9, bg: () => <LogoCard src="img/logo_gta6.png" sub="Grand Theft Auto VI" color="pink" dur={63} />, fx: 'flash', sfx: ['impact_trailer']},
  {t: 36.0, bg: B(v('neon_biker', {kb: 'in'})), fg: [K(['*GTA 6*'], {size: 280, color: 'pink', top: 420})], fx: 'glitch', sfx: ['glitch3', 'bass_hit2']},
  {t: 39.3, bg: B(v('child_gaming_chair', {kb: 'in'})), fg: [K(['SHUNCHAKI', 'O‘YIN *EMAS*'], {size: 140})], fx: 'zoom', sfx: ['whoosh5']},
  {t: 41.9, bg: B(v('cash_rotating', {kb: 'in', grade: 'warm'})), fg: [K(['*MILLIARDLAB $*', 'DAROMAD'], {size: 130})], fx: 'flash', sfx: ['coin', 'whoosh3']},
  {t: 44.2, bg: B(v('boy_gaming', {kb: 'in', grade: 'warm'})), fg: [CO('Bir avlodning', 'bolaligi', {top: 260, color: 'orange'})], fx: 'blur', sfx: ['sweep2']},
  {t: 46.5, bg: B(v('stock_graph', {kb: 'up'})), fg: [K(['*REKORDLAR*', 'O‘RNATGAN', 'FRANSHIZA'], {size: 130, color: 'green'})], fx: 'zoom', sfx: ['whoosh4']},
  {t: 50.7, bg: B(v('confused_laptop', {kb: 'in', dim: 0.15})), fg: [K(['GTA *QANDAY*', 'YARATILGAN?'], {size: 130, color: 'cyan'})], fx: 'glitch', sfx: ['glitch1']},
  {t: 54.0, bg: B(v('building_burning', {kb: 'in'})), fg: [K(['NEGA DEYARLI', '*MUVAFFAQIYATSIZ*?'], {size: 104, color: 'pink'})], fx: 'flash', sfx: ['impact_zoom']},
  {t: 57.2, bg: B(v('la_highway_sea', {kb: 'left', grade: 'warm'})), fg: [K(['*SAN ANDREAS*', 'NEGA MASHHUR?'], {size: 120, color: 'orange'})], fx: 'whip', sfx: ['whoosh2']},
  {t: 60.9, bg: B(v('money_counter', {kb: 'in'})), fg: [K(['*GTA 5*', 'ENG KATTA', 'LOYIHA?'], {size: 130, color: 'green'})], fx: 'zoom', sfx: ['coin']},
  {t: 65.7, bg: B(v('hourglass_close', {kb: 'in'})), fg: [K(['GTA 6 NEGA', 'SHUNCHA', '*KUTTIRDI*?'], {size: 130, color: 'pink'})], fx: 'blur', sfx: ['heartbeat']},
  {t: 69.7, bg: B(v('aerial_traffic_night', {kb: 'in', dim: 0.45})), fg: [{el: () => <Chapter num="Bugun ko‘rib chiqamiz" title="GTA tarixi 1997 — 2026" />}], fx: 'leak', sfx: ['orch_transition']},
  {t: 76.0, bg: B(v('lightning', {kb: 'in', dim: 0.2})), fg: [{el: () => <TimedList title="Bu tarixda" items={[{text: 'Tasodifiy kashfiyotlar', at: 0.2}, {text: 'Ulkan tavakkalchiliklar', at: 2.3}, {text: 'Milliardlab dollarlar', at: 4.3}, {text: 'Hayratli qarorlar', at: 6.6}]} />}], fx: 'zoom', sfx: ['bass_hit']},

  // ============================ 1. DANDI / DMA ============================
  {t: 84.2, bg: B(im('dundee_tay_bridge.jpg', {kb: 'in', dim: 0.35, grade: 'teal'})), fg: [{el: () => <Chapter num="1-qism" title="Hammasi qayerdan boshlangan?" color="cyan" />}], fx: 'leak', sfx: ['impact_deep', 'whoosh1'], chapter: '1'},
  {t: 88.8, bg: B(v('ghetto_blaster', {kb: 'in', dim: 0.45, grade: 'warm'})), fg: [{el: () => <YearStamp year={1995} label="1990-yillar o‘rtasi" prev={2026} color="cyan" />}], fx: 'whip', sfx: ['whoosh3', 'riser_short']},
  {t: 91.5, bg: () => <MapScene center={[-3.2, 56.5]} scaleFrom={700} scaleTo={6500} highlight={['United Kingdom']} pins={[{name: 'Dandi', lon: -2.97, lat: 56.46, sub: 'Shotlandiya'}]} title="Shotlandiya" color="cyan" />, fx: 'zoom', sfx: ['sweep1']},
  {t: 94.0, bg: B(im('dma_team_2011.jpg', {kb: 'in', focus: '50% 40%'})), fg: [CO('DMA Design', 'jamoa a’zolari (2011-yilgi surat)', {top: 250, color: 'cyan'})], fx: 'flash', sfx: ['shutter', 'whoosh2']},
  {t: 97.8, bg: B(v('aerial_city_night_top', {kb: 'in'})), fg: [K(['*OCHIQ*', 'SHAHAR'], {size: 170, color: 'cyan'})], fx: 'whip', sfx: ['whoosh4']},
  {t: 102.1, bg: B(v('police_lights', {kb: 'in'})), fg: [K(['POLITSIYA', '*TA’QIBI*'], {size: 160, color: 'cyan'})], fx: 'flash', sfx: ['siren_short']},
  {t: 105.3, bg: B(v('vhs_neon_palm', {kb: 'in', dim: 0.4})), fg: [CO('Dastlabki nom', undefined, {top: 300, until: 0.3}), K(['*RACE’N’CHASE*'], {size: 140, top: 420, at: 0.3})], fx: 'glitch', sfx: ['glitch2', 'bass_hit']},
  {t: 108.2, bg: B(v('matrix_screens', {kb: 'in'})), fg: [K(['*QIZIQ*', 'HOLAT'], {size: 170})], fx: 'glitch', sfx: ['glitch3']},
  {t: 111.3, bg: () => <PixelCity mode="chase" />, fg: [CO('Texnik xato', 'politsiya haddan tashqari agressiv', {top: 230, color: 'pink'})], fx: 'shake', sfx: ['siren', 'car_by']},
  {t: 118.7, bg: B(v('friends_gaming', {kb: 'in'})), fg: [K(['KUTILMAGAN XATO', '→ *QIZIQARLI*'], {size: 110, color: 'green'})], fx: 'flash', sfx: ['impact_zoom']},
  {t: 123.0, bg: (d) => <Split a={{...v('red_sports_car_road'), label: 'Oddiy poyga'}} b={{...v('police_blurry', {kb: 'in'}), label: 'Politsiyadan qochish'}} bAt={3.4} dur={d} color="cyan" />, fx: 'whip', sfx: ['whoosh1', 'siren_short']},
  {t: 131.6, bg: B(v('brainstorm', {fit: 'card', kb: 'in'})), fg: [K(['G‘OYA', '*O‘ZGARDI*'], {size: 150, top: 1000 - 640})], fx: 'zoom', sfx: ['sweep2']},
  {t: 134.6, bg: () => <LogoCard src="img/logo_gta_series.png" sub="1997 · Birinchi o‘yin" dur={144} />, fx: 'flash', sfx: ['impact_trailer']},
  {t: 139.4, bg: () => <PixelCity mode="top" />, fg: [{el: () => <TimedList items={[{text: 'Mashina o‘g‘irlash', at: 1.0}, {text: 'Topshiriqlar', at: 2.0}, {text: 'Katta shahar', at: 3.3}]} top={250} size={58} />}], fx: 'glitch', sfx: ['pixel_boom']},
  {t: 145.3, bg: B(im('ps1.jpg', {fit: 'card', kb: 'in'})), fg: [CO('1997-yil', 'o‘sha davr texnologiyasi', {top: 250})], fx: 'whip', sfx: ['whoosh5']},
  {t: 149.1, bg: B(v('neon_drive', {kb: 'in'})), fg: [K(['BITTA', '*KUCHLI* G‘OYA'], {size: 140})], fx: 'zoom', sfx: ['bass_hit2']},
  {t: 152.7, bg: B(v('dashboard_accel', {kb: 'in'})), fg: [K(['BELGILANGAN', 'YO‘L *YO‘Q*'], {size: 140, color: 'pink'})], fx: 'whip', sfx: ['car_by']},
  {t: 155.8, bg: B(v('aerial_city_night', {kb: 'out', from: 8})), fg: [K(['O‘Z YO‘LINGNI', '*O‘ZING* TANLA'], {size: 120})], fx: 'zoom', sfx: ['whoosh2']},
  {t: 158.4, bg: B(v('sea_sunset', {kb: 'in', from: 6})), fg: [K(['*ERKINLIK*'], {size: 220, color: 'green', top: 440})], fx: 'flash', sfx: ['impact_deep']},
  {t: 163.4, bg: B(v('lightning', {kb: 'out', from: 3})), fg: [K(['BU HALI', '*BOSHLANISH* EDI'], {size: 120})], fx: 'blur', sfx: ['riser_synth']},
  {t: 165.2, bg: B(v('fireball', {kb: 'in'})), fg: [K(['HAQIQIY', '*INQILOB*'], {size: 180})], fx: 'shake', sfx: ['impact_big']},

  // ============================ 2. GTA III / VICE CITY ============================
  {t: 169.3, bg: B(v('ny_night_pan', {kb: 'in', dim: 0.5})), fg: [{el: () => <YearStamp year={2001} prev={1997} />}], fx: 'flash', sfx: ['bass_hit'], chapter: '2'},
  {t: 170.7, bg: () => <LogoCard src="img/logo_gta3.png" sub="Uch o‘lchamli inqilob" dur={84} />, fx: 'glitch', sfx: ['impact_trailer']},
  {t: 173.5, bg: () => <PixelCity mode="tilt" />, fg: [{at: 0, until: 2.5, el: () => <Callout title="2D · yuqoridan" top={230} />}, {at: 3.2, el: () => <Callout title="3D · uch o‘lchamli" top={230} color="green" />}], fx: 'zoom', sfx: ['riser_stutter']},
  {t: 179.9, bg: B(v('street_night_traffic', {kb: 'in'})), fg: [{el: () => <TimedList items={[{text: 'Ko‘chada yurish', at: 0.1}, {text: 'Mashina haydash', at: 1.5}, {text: 'Topshiriqlar', at: 3.0}, {text: 'Istalgan tomonga', at: 4.1}]} top={260} size={58} />}], fx: 'whip', sfx: ['whoosh3']},
  {t: 186.7, bg: B(v('empire_timelapse', {kb: 'in'})), fg: [CO('Liberty City', 'xayoliy shahar', {top: 250})], fx: 'zoom', sfx: ['whoosh1']},
  {t: 188.8, bg: () => <MapScene center={[-74, 40.7]} scaleFrom={500} scaleTo={5000} highlight={['United States of America']} pins={[{name: 'Nyu-York', lon: -74, lat: 40.71, sub: 'Liberty City ilhomi'}]} title="AQSh" />, fx: 'zoom', sfx: ['sweep1']},
  {t: 190.6, bg: B(v('times_square_ads', {kb: 'in'})), fg: [K(['NIHOYATDA', '*YANGILIK*'], {size: 150})], fx: 'flash', sfx: ['whoosh4']},
  {t: 194.7, bg: B(v('liberty_brooklyn', {kb: 'left', dim: 0.15})), fg: [K(['OCHIQ DUNYOGA', '*ULKAN* TA’SIR'], {size: 120})], fx: 'zoom', sfx: ['bass_hit2']},
  {t: 199.1, bg: B(im('rockstar_north_2023.jpg', {kb: 'in'})), fg: [{el: () => <Callout title="Rockstar Games" sub="to‘xtab qolmadi" top={250} />}], fx: 'whip', sfx: ['whoosh2']},
  {t: 202.7, bg: B(v('vhs_palm_island', {kb: 'in', dim: 0.4})), fg: [{el: () => <YearStamp year={2002} prev={2001} color="pink" />}], fx: 'flash', sfx: ['bass_hit']},
  {t: 204.2, bg: () => <LogoCard src="img/logo_vicecity.png" width={560} color="pink" bg={v('vhs_sun_palms', {from: 5})} dur={75} />, fx: 'glitch', sfx: ['impact_trailer', 'glitch2']},
  {t: 206.7, bg: B(v('vhs_neon_palm', {kb: 'out', from: 4})), fg: [K(['*1980*-YILLAR'], {size: 160, color: 'pink'})], fx: 'zoom', sfx: ['whoosh3']},
  {t: 209.6, bg: () => <MapScene center={[-80.5, 26.5]} scaleFrom={600} scaleTo={5200} highlight={['United States of America']} pins={[{name: 'Miami', lon: -80.19, lat: 25.76, sub: 'Vice City ilhomi'}]} title="Florida" color="pink" />, fx: 'zoom', sfx: ['sweep2']},
  {t: 212.5, bg: B(v('miami_nightlife', {kb: 'in'})), fg: [K(['*NEON*'], {size: 220, color: 'pink', top: 460})], fx: 'flash', sfx: ['whoosh5']},
  {t: 214.1, bg: B(v('white_sportscar_sunset', {kb: 'in'})), fg: [K(['SPORT', '*AVTO*'], {size: 170, color: 'orange'})], fx: 'whip', sfx: ['car_by']},
  {t: 215.3, bg: B(v('beach_sunset', {kb: 'in'})), fg: [K(['*PLYAJLAR*'], {size: 170, color: 'pink', top: 460})], fx: 'whip', sfx: ['whoosh2']},
  {t: 216.3, bg: B(v('miami_night_lights', {kb: 'in'})), fg: [K(['MUSIQA &', '*JINOYAT* OLAMI'], {size: 120, color: 'pink'})], fx: 'flash', sfx: ['bass_hit2']},
  {t: 218.1, bg: B(v('miami_calm_night', {kb: 'in', dim: 0.35})), fg: [K(['BOSH QAHRAMON:', '*TOMMY*', '*VERCETTI*'], {size: 130, color: 'pink'})], fx: 'zoom', sfx: ['impact_zoom']},
  {t: 220.7, bg: B(v('pink_sunset_car', {kb: 'in', rate: 0.9})), fg: [CO('Oddiy topshiriqlardan', 'boshlaydi', {top: 260, color: 'pink'})], fx: 'whip', sfx: ['whoosh1']},
  {t: 223.3, bg: B(v('red_luxury_spotlight', {kb: 'in'})), fg: [K(['JINOYAT OLAMIDA', '*KUCHLI* SHAXS'], {size: 120, color: 'pink'})], fx: 'flash', sfx: ['bass_hit']},
  {t: 226.8, bg: B(v('vhs_sun_palms', {kb: 'out', from: 9})), fg: [K(['ENG KATTA YUTUQ:', '*ATMOSFERA*'], {size: 120, color: 'pink'})], fx: 'zoom', sfx: ['whoosh4']},
  {t: 230.9, bg: B(v('theater_audience', {kb: 'in', grade: 'warm'})), fg: [K(['GO‘YOKI', '*JINOYAT FILMI*'], {size: 120, color: 'orange', at: 2.9})], fx: 'blur', sfx: ['sweep1']},
  {t: 238.0, bg: B(v('florida_sunset', {kb: 'in'})), fg: [K(['ENG ESDA QOLARLISI', 'HALI *OLDINDA*'], {size: 110})], fx: 'zoom', sfx: ['riser_synth']},

  // ============================ 3. SAN ANDREAS ============================
  {t: 243.1, bg: B(v('la_downtown_drone', {kb: 'in', dim: 0.5})), fg: [{el: () => <YearStamp year={2004} prev={2002} color="orange" />}], fx: 'flash', sfx: ['impact_big'], chapter: '3'},
  {t: 244.7, bg: B(v('hollywood_sign_fly', {kb: 'in', dim: 0.3})), fg: [K(['GRAND THEFT AUTO:', '*SAN ANDREAS*'], {size: 120, color: 'orange'})], fx: 'glitch', sfx: ['bass_hit2']},
  {t: 247.4, bg: B(v('gamers_room', {kb: 'in', grade: 'warm'})), fg: [K(['BOLALIK', '*XOTIRALARI*'], {size: 140, color: 'orange'})], fx: 'blur', sfx: ['whoosh5']},
  {t: 250.9, bg: B(v('hands_pc_game', {kb: 'in'})), fg: [CO('Kompyuter klublari', undefined, {top: 260, color: 'orange'})], fx: 'whip', sfx: ['type_click']},
  {t: 252.3, bg: B(v('friends_gaming', {kb: 'left', from: 6})), fg: [CO('Do‘stlar bilan', undefined, {top: 260, color: 'orange'})], fx: 'whip', sfx: ['whoosh3']},
  {t: 254.1, bg: B(v('drift_aerial', {kb: 'in'})), fg: [CO('Mashinalar', undefined, {top: 260, color: 'orange'})], fx: 'whip', sfx: ['car_by']},
  {t: 255.1, bg: B(v('police_lights2', {kb: 'out', from: 5, dim: 0.35})), fg: [{el: () => <Quote text="HESOYAM · AEZAKMI · BAGUVIX" who="mashhur kodlar" color="orange" top={300} />}], fx: 'glitch', sfx: ['typing']},
  {t: 257.2, bg: B(v('la_avenue_night', {kb: 'in', dim: 0.3})), fg: [K(['ENG MUHIMI...'], {size: 110, until: 1.4}), K(['*CJ*'], {size: 300, color: 'green', top: 520, at: 1.4}), CO('Carl Johnson', undefined, {top: 900, color: 'green', at: 2.2})], fx: 'zoom', sfx: ['bass_hit', 'impact_zoom']},
  {t: 260.9, bg: () => <MapScene center={[-118.3, 34.05]} scaleFrom={600} scaleTo={6000} highlight={['United States of America']} pins={[{name: 'Los Santos', lon: -118.24, lat: 34.05, sub: 'Los-Anjeles asosida'}]} title="Kaliforniya" color="green" />, fx: 'zoom', sfx: ['sweep1']},
  {t: 265.3, bg: B(v('handcuffed', {kb: 'in', dim: 0.2})), fg: [{el: () => <TimedList items={[{text: 'Eski do‘stlar', at: 0.1}, {text: 'Oila', at: 1.5}, {text: 'Ko‘cha guruhlari', at: 2.4}]} top={280} color="green" />}], fx: 'whip', sfx: ['whoosh2']},
  {t: 270.8, bg: B(v('newspaper_pov', {kb: 'in'})), fg: [K(['FAQAT HIKOYA', '*EMAS*'], {size: 140, color: 'green'})], fx: 'zoom', sfx: ['sweep2']},
  {t: 274.8, bg: B(v('gamer_hands', {kb: 'in', dim: 0.55})), fg: [{el: () => <IconGrid title="Ancha katta imkoniyatlar" color="green" items={[{label: 'Sport zali', icon: 'gym', at: 5.5}, {label: 'Ovqatlanish', icon: 'food', at: 7.2}, {label: 'Kiyimlar', icon: 'shirt', at: 8.2}, {label: 'Soch turmagi', icon: 'hair', at: 9.8}, {label: 'Avto sozlash', icon: 'car', at: 11.6}, {label: '3 ta shahar', icon: 'city', at: 13.0}]} />}], fx: 'zoom', sfx: ['bass_hit2']},
  {t: 290.8, bg: (d) => <Panels dur={d} panels={[{...v('la_downtown_drone', {from: 6}), name: 'Los Santos', at: 0, color: 'green'}, {...v('avenue_night'), name: 'San Fierro', at: 1.5, color: 'cyan'}, {...v('aerial_city_night', {from: 4}), name: 'Las Venturas', at: 2.4, color: 'yellow'}]} />, fx: 'whip', sfx: ['whoosh1', 'whoosh3']},
  {t: 294.4, bg: B(v('malibu_coast', {kb: 'in'})), fg: [{el: () => <TimedList title="Bundan tashqari" items={[{text: 'Qishloqlar', at: 1.1}, {text: 'Tog‘lar', at: 1.9}, {text: 'Cho‘llar', at: 2.7}, {text: 'Aeroportlar', at: 3.4}]} color="green" />}], fx: 'zoom', sfx: ['sweep1']},
  {t: 299.8, bg: B(v('man_controller', {kb: 'in'})), fg: [K(['O‘ZIGA XOS', '*VIRTUAL HAYOT*'], {size: 120, color: 'green'})], fx: 'flash', sfx: ['impact_zoom']},
  {t: 305.2, bg: B(im('rockstar_fan.jpg', {kb: 'up', focus: '50% 30%'})), fg: [K(['ENG *SEVIMLI*', 'QISMLARDAN BIRI'], {size: 110, color: 'green'})], fx: 'zoom', sfx: ['whoosh4']},

  // ============================ 4. GTA IV ============================
  {t: 311.3, bg: B(v('servers', {kb: 'in'})), fg: [K(['TEXNOLOGIYALAR', '*RIVOJLANDI*'], {size: 120, color: 'cyan'})], fx: 'glitch', sfx: ['glitch1'], chapter: '4'},
  {t: 314.1, bg: B(v('ny_night_pan', {kb: 'in', from: 12, dim: 0.35})), fg: [{until: 1.3, el: () => <YearStamp year={2008} prev={2004} />}, K(['GTA *IV*'], {size: 240, top: 420, at: 1.2}), CO('Niko Bellic', 'muhojir', {top: 900, at: 4.1, color: 'cyan'})], fx: 'flash', sfx: ['impact_big']},
  {t: 320.8, bg: B(v('liberty_brooklyn', {kb: 'in', from: 6})), fg: [K(['AMERIKADA', '*YANGI HAYOT*'], {size: 130, color: 'cyan'})], fx: 'zoom', sfx: ['whoosh2']},
  {t: 323.2, bg: (d) => <Split a={{...v('florida_sunset', {from: 6}), label: 'Orzu'}} b={{...v('police_lights', {from: 4}), label: 'Haqiqat'}} bAt={1.6} dur={d} color="pink" />, fx: 'whip', sfx: ['whoosh3', 'bass_hit2']},
  {t: 328.5, bg: B(v('newspaper_face', {kb: 'in', grade: 'mono'})), fg: [K(['*JIDDIYROQ*', 'DRAMATIKROQ'], {size: 140})], fx: 'blur', sfx: ['sweep2']},
  {t: 334.1, bg: B(v('la_freeway_traffic', {kb: 'in', dim: 0.25})), fg: [{el: () => <TimedList items={[{text: 'Avtomobil harakati', at: 0.1}, {text: 'Odamlar reaksiyasi', at: 1.3}, {text: 'Fizika tizimi', at: 2.8}]} top={280} color="cyan" />}], fx: 'whip', sfx: ['car_by']},
  {t: 340.6, bg: B(v('la_helipads', {kb: 'in'})), fg: [K(['KATTA XARITA EMAS —', '*ISHONARLI* XARITA'], {size: 100, color: 'cyan'})], fx: 'zoom', sfx: ['whoosh1']},

  // ============================ 5. GTA V ============================
  {t: 347.8, bg: B(v('fireworks_black', {kb: 'in', dim: 0.2})), fg: [{at: 1.5, el: () => <YearStamp year={2013} prev={2008} color="green" />}], fx: 'blur', sfx: ['riser_synth'], chapter: '5'},
  {t: 351.4, bg: B(v('fireworks_city', {kb: 'in'})), fg: [K(['GTA *V*'], {size: 300, color: 'green', top: 400})], fx: 'shake', sfx: ['impact_trailer']},
  {t: 354.0, bg: B(v('gamer_frustrated', {kb: 'in'})), fg: [K(['SANOATNI', '*LARZAGA* SOLDI'], {size: 120, color: 'green'})], fx: 'shake', sfx: ['impact_deep']},
  {t: 356.0, bg: B(v('neon_speedometer', {kb: 'in', dim: 0.3})), fg: [K(['BITTA EMAS —', '*3 TA* BOSH', 'QAHRAMON'], {size: 120, color: 'green'})], fx: 'zoom', sfx: ['bass_hit']},
  {t: 359.4, bg: (d) => <Panels dur={d} panels={[{...v('la_highway_sea', {from: 3}), name: 'Michael', at: 0, color: 'cyan'}, {...v('street_night_traffic', {from: 5}), name: 'Franklin', at: 0.9, color: 'green'}, {...v('drift_country'), name: 'Trevor', at: 2.0, color: 'orange'}]} />, fg: [CO('O‘z xarakteri', 'muammolari va maqsadlari', {top: 900, at: 4.1})], fx: 'whip', sfx: ['whoosh1', 'whoosh3', 'whoosh5']},
  {t: 366.6, bg: B(v('video_editing', {fit: 'card', kb: 'in'})), fg: [K(['QAHRAMONLAR', 'ORASIDA *ALMASHISH*'], {size: 100, color: 'green', top: 1000 - 680})], fx: 'zoom', sfx: ['sweep1']},
  {t: 371.6, bg: B(v('la_downtown_drone', {kb: 'out', from: 10})), fg: [K(['*KATTAROQ*', 'BATAFSILROQ'], {size: 150, color: 'green'})], fx: 'flash', sfx: ['whoosh4']},
  {t: 376.7, bg: B(v('hollywood_sign_fly', {kb: 'left', from: 8})), fg: [{el: () => <TimedList items={[{text: 'Tog‘lar', at: 0}, {text: 'Okean', at: 0.9}, {text: 'Aeroportlar', at: 1.8}, {text: 'Shahar markazi', at: 2.3}, {text: 'Cho‘llar', at: 3.2}]} top={250} size={54} color="green" />}], fx: 'whip', sfx: ['whoosh2']},
  {t: 382.3, bg: B(v('money_counter', {kb: 'out', from: 5})), fg: [K(['*MOLIYAVIY*', 'MUVAFFAQIYAT'], {size: 130, color: 'green'})], fx: 'zoom', sfx: ['coin']},
  {t: 387.5, bg: B(v('banknotes_falling', {kb: 'in', from: 6, dim: 0.35, grade: 'warm'})), fg: [{el: () => <Counter to={1000000000} prefix="$" label="Atigi 3 kunda" sub="savdo" color="green" countDur={60} />}], fx: 'flash', sfx: ['riser_short', 'money_bag']},
  {t: 392.9, bg: B(v('stock_graph', {kb: 'in', from: 4})), fg: [K(['TARIXDAGI', '*ENG TEZ*', 'MILLIARD'], {size: 140, color: 'green'})], fx: 'zoom', sfx: ['bass_hit2']},
  {t: 398.1, bg: B(v('reel_counter', {kb: 'in', dim: 0.45})), fg: [{el: () => <Counter to={230} suffix=" MLN+" label="2026-yil noyabr" sub="sotilgan nusxa" color="yellow" countDur={70} />}], fx: 'whip', sfx: ['riser_short', 'ding']},
  {t: 404.7, bg: B(v('digital_counter', {kb: 'in', dim: 0.4})), fg: [{el: () => <Counter to={10} suffix="+ YIL" label="2013-yildan beri" sub="eng mashhurlar qatorida" color="cyan" countDur={40} />}], fx: 'zoom', sfx: ['ding']},
  {t: 412.6, bg: B(v('gamers_room', {kb: 'left', from: 4})), fg: [K(['GTA *ONLINE*'], {size: 190, color: 'cyan', top: 440})], fx: 'glitch', sfx: ['glitch2', 'bass_hit']},
  {t: 415.6, bg: B(v('aerial_city_night_top', {kb: 'out', from: 4, dim: 0.5})), fg: [{el: () => <IconGrid title="Internet orqali" color="cyan" items={[{label: 'Birgalikda topshiriq', icon: 'users', at: 2.6}, {label: 'Avto xaridi', icon: 'cart', at: 4.8}, {label: 'Biznes', icon: 'briefcase', at: 5.9}, {label: 'Musobaqalar', icon: 'trophy', at: 7.0}]} />}], fx: 'zoom', sfx: ['whoosh3']},
  {t: 425.5, bg: B(v('programmer_big', {kb: 'in'})), fg: [K(['YILLAR DAVOMIDA', '*YANGILANISHLAR*'], {size: 100, color: 'cyan'})], fx: 'whip', sfx: ['type_click']},

  // ============================ 6. GTA VI ============================
  {t: 430.4, bg: B(v('phone_night', {kb: 'in'})), fg: [K(['MUXLISLARNING', '*BITTA* SAVOLI'], {size: 120, color: 'pink'})], fx: 'zoom', sfx: ['heartbeat'], chapter: '6'},
  {t: 434.0, bg: () => <BigWord text="GTA 6 qachon?" color="pink" size={200} />, fx: 'shake', sfx: ['impact_big']},
  {t: 436.4, bg: B(im('ps4.jpg', {fit: 'card', kb: 'in'})), fg: [CO('Yillar o‘tdi', undefined, {top: 260, color: 'pink'})], fx: 'whip', sfx: ['whoosh5']},
  {t: 437.9, bg: B(im('xbox_series.jpg', {kb: 'in'})), fg: [CO('Yangi konsollar', undefined, {top: 260, color: 'pink'})], fx: 'whip', sfx: ['whoosh1']},
  {t: 439.4, bg: B(v('code_closeup', {kb: 'in'})), fg: [CO('Texnologiyalar', undefined, {top: 260, color: 'pink'})], fx: 'whip', sfx: ['whoosh3']},
  {t: 441.0, bg: B(v('hourglass_close', {kb: 'out', from: 4, dim: 0.2})), fg: [K(['RASMIY MA’LUMOT', '*JUDA KAM*'], {size: 120, color: 'pink'})], fx: 'zoom', sfx: ['sweep2']},
  {t: 445.4, bg: B(v('green_code', {kb: 'in', dim: 0.3})), fg: [{el: () => <YearStamp year={2022} prev={2013} color="green" />}], fx: 'glitch', sfx: ['glitch1', 'bass_hit']},
  {t: 447.3, bg: B(v('matrix_screens', {kb: 'in', from: 4, dim: 0.45})), fg: [{el: () => <HackUI title="KIBER HUJUM" lines={['> connection from unknown host', '> access: development server', '! WARNING: data breach detected', '> uploading gameplay_dev.mp4 ...', '> uploading gameplay_dev_02.mp4 ...', '! LEAK IN PROGRESS']} />}], fx: 'glitch', sfx: ['glitch2', 'typing']},
  {t: 453.9, bg: B(v('green_code', {kb: 'out', from: 5})), fg: [K(['ENG *SHOV-SHUVLI*', 'SIZIB CHIQISH'], {size: 110, color: 'green'})], fx: 'glitch', sfx: ['glitch3', 'impact_zoom']},
  {t: 458.2, bg: B(v('confused_laptop', {kb: 'out', from: 5})), fg: [CO('Norasmiy videolar', 'muxlislar ilk bor ko‘rishdi', {top: 260, color: 'pink'})], fx: 'zoom', sfx: ['sweep1']},
  {t: 464.5, bg: dark(), fg: [{until: 2.6, el: () => <YearStamp year={2023} prev={2022} label="Dekabr" color="pink" />}], fx: 'flash', sfx: ['bass_hit']},
  {t: 467.2, bg: () => <TrailerUI logo="img/logo_gta6.png" label="Birinchi rasmiy treyler" />, fx: 'zoom', sfx: ['shutter', 'riser_short']},
  {t: 470.6, bg: B(v('fireworks_city', {kb: 'in', from: 6})), fg: [K(['INTERNET', '*PORTLADI*'], {size: 170, color: 'pink'})], fx: 'shake', sfx: ['impact_big']},
  {t: 473.0, bg: () => <LogoCard src="img/logo_vicecity.png" width={460} sub="Vice City qaytdi" color="pink" bg={v('miami_night_lights', {from: 5})} dur={135} />, fx: 'glitch', sfx: ['glitch1', 'bass_hit2']},
  {t: 477.5, bg: B(v('palm_sun', {kb: 'up'})), fg: [{el: () => <TimedList title="Zamonaviy Amerika" items={[{text: 'Ijtimoiy tarmoqlar', at: 3.1}, {text: 'Plyajlar', at: 4.4}, {text: 'Avtomobillar', at: 5.3}, {text: 'Rang-barang odamlar', at: 6.6}]} color="pink" />}], fx: 'zoom', sfx: ['whoosh2']},
  {t: 487.5, bg: B(v('pink_sunset_car', {kb: 'out', from: 1})), fg: [K(['*LUCIA*'], {size: 260, color: 'pink', top: 420}), CO('Ayol bosh qahramon', undefined, {top: 760, color: 'pink', at: 3.0})], fx: 'flash', sfx: ['impact_zoom']},
  {t: 491.9, bg: B(v('red_sports_car_road', {kb: 'in', from: 2})), fg: [K(['*JASON*'], {size: 260, color: 'orange', top: 420}), CO('Ikkinchi bosh qahramon', undefined, {top: 760, color: 'orange', at: 1.5})], fx: 'flash', sfx: ['impact_zoom']},
  {t: 495.8, bg: B(v('police_blurry', {kb: 'out', from: 4})), fg: [K(['MUNOSABATLAR +', '*JINOYAT* OLAMI'], {size: 110, color: 'pink'})], fx: 'zoom', sfx: ['siren_short']},
  {t: 501.7, bg: () => <MapScene center={[-81.5, 27.5]} scaleFrom={600} scaleTo={4200} highlight={['United States of America']} pins={[{name: 'Leonida', lon: -81.4, lat: 27.9, sub: 'Florida ilhomi'}]} title="AQSh · Florida" color="pink" />, fx: 'zoom', sfx: ['sweep1']},
  {t: 507.1, bg: B(v('miami_nightlife', {kb: 'left', from: 6})), fg: [K(['OCHIQ DUNYO +', '*JAMIYAT* SATIRASI'], {size: 110, color: 'pink'})], fx: 'whip', sfx: ['whoosh4']},
  {t: 514.5, bg: () => <DateShift items={[{text: '2025', at: 4.2, crossAt: 6.4}, {text: 'MAY 2026', at: 8.1, crossAt: 9.1}, {text: '19.11.2026', at: 11.8}]} final={{text: '19.11.2026', at: 15.8, sub: 'Yetib keldi'}} />, fx: 'zoom', sfx: ['type_click']},
  {t: 533.7, bg: () => <Platforms imgsAt={5.8} chips={[{text: 'Chiqish treyleri', at: 2.1}, {text: 'Oldindan yuklash', at: 4.2}, {text: 'PlayStation 5', at: 5.8}, {text: 'Xbox Series X|S', at: 7.7}]} />, fx: 'flash', sfx: ['impact_trailer']},

  // ============================ 7. NEGA SHUNCHA VAQT ============================
  {t: 544.3, bg: B(v('hourglass_finish', {kb: 'out', from: 3, dim: 0.25})), fg: [K(['NEGA SHUNCHA', '*VAQT* KERAK BO‘LDI?'], {size: 110, color: 'cyan'})], fx: 'blur', sfx: ['heartbeat'], chapter: '7'},
  {t: 550.2, bg: B(v('servers', {kb: 'out', from: 4})), fg: [K(['*NIHOYATDA*', 'MURAKKAB'], {size: 160, color: 'cyan'})], fx: 'glitch', sfx: ['glitch3']},
  {t: 555.1, bg: B(v('dev_screen', {kb: 'left', from: 6, dim: 0.6})), fg: [{el: () => <IconGrid color="cyan" linkAt={12.4} top={220} items={[{label: 'Minglab obyektlar', icon: 'cube', at: 0}, {label: 'Avto harakati', icon: 'car', at: 1.4}, {label: 'Sun’iy intellekt', icon: 'brain', at: 3.0}, {label: 'Yoritish', icon: 'light', at: 6.0}, {label: 'Ovoz yozish', icon: 'mic', at: 7.4}, {label: 'Animatsiya', icon: 'film', at: 8.4}, {label: 'Shahar dizayni', icon: 'city', at: 9.6}, {label: 'Hikoya', icon: 'book', at: 11.2}]} />}], fx: 'zoom', sfx: ['bass_hit2']},
  {t: 570.5, bg: () => <PixelCity mode="sim" rainAt={10.6} labels={[{text: 'Mashinalar', at: 3.2, x: 120, y: 330}, {text: 'Piyodalar', at: 5.4, x: 560, y: 460}, {text: 'Svetoforlar', at: 6.6, x: 140, y: 620}, {text: 'Politsiya', at: 8.1, x: 560, y: 760}, {text: 'Ob-havo', at: 10.6, x: 300, y: 900}]} />, fx: 'zoom', sfx: ['car_by']},
  {t: 582.3, bg: B(v('neon_speedometer', {kb: 'out', from: 4})), fg: [K(['HAMMASI', '*REAL VAQTDA*'], {size: 130, color: 'cyan'})], fx: 'flash', sfx: ['bass_hit']},
  {t: 585.8, bg: B(v('programmer_hands', {kb: 'in', from: 3})), fg: [K(['KO‘P *YILLIK*', 'MEHNAT'], {size: 150, color: 'cyan'})], fx: 'zoom', sfx: ['whoosh1']},
  {t: 590.5, bg: B(v('cash_rotating', {kb: 'out', from: 5, dim: 0.5})), fg: [{until: 7.2, el: () => <Counter from={1} to={2} decimals={0} prefix="$" suffix=" MLRD?" label="Internetdagi taxminlar" sub="1 yoki hatto 2 milliard" color="yellow" countDur={130} />}, {at: 7.3, el: () => <Kinetic lines={['RASMAN', '*TASDIQLANMAGAN*']} color="pink" size={120} />}], fx: 'zoom', sfx: ['coin', 'impact_zoom']},
  {t: 604.2, bg: () => <LogoCard src="img/logo_gta6.png" sub="Eng katta loyihalardan biri" color="pink" dur={183} />, fx: 'flash', sfx: ['impact_trailer']},

  // ============================ 8. XULOSA ============================
  {t: 610.3, bg: () => <TimelineRecap items={[{year: '1997', title: 'Yuqoridan shahar', at: 3.0, color: 'yellow'}, {year: '2001', title: 'Liberty City · 3D', at: 7.2, color: 'cyan'}, {year: '2002', title: 'Vice City', at: 10.8, color: 'pink'}, {year: '2004', title: 'San Andreas', at: 13.7, color: 'orange'}, {year: '2008', title: 'GTA IV', at: 16.0, color: 'cyan'}, {year: '2013', title: 'GTA 5', at: 18.8, color: 'green'}, {year: '2026', title: 'GTA 6', at: 22.0, color: 'pink'}]} />, fx: 'leak', sfx: ['orch_transition'], chapter: '8'},
  {t: 635.5, bg: B(v('aerial_city_night', {kb: 'in', from: 6})), fg: [K(['KICHIK TAJRIBADAN', '*GLOBAL BRENDGA*'], {size: 110})], fx: 'zoom', sfx: ['riser_synth']},
  {t: 642.9, bg: () => <BigWord text="Siri nimada?" color="yellow" size={190} />, fx: 'shake', sfx: ['bass_hit']},
  {t: 644.2, bg: B(v('neon_drive', {kb: 'out', from: 5})), fg: [K(['GRAFIKADAMI?'], {size: 140})], fx: 'whip', sfx: ['whoosh5']},
  {t: 645.8, bg: B(v('red_luxury_spotlight', {kb: 'out', from: 4})), fg: [K(['MASHINALAR', 'VA QUROLLARDAMI?'], {size: 110})], fx: 'whip', sfx: ['whoosh3']},
  {t: 647.9, bg: () => <BigWord text="Yo‘q." color="pink" size={300} />, fx: 'shake', sfx: ['impact_big']},
  {t: 648.7, bg: B(v('sea_sunset', {kb: 'out', from: 14})), fg: [K(['*ERKINLIK*', 'HISSI'], {size: 190, color: 'green'})], fx: 'flash', sfx: ['impact_deep']},
  {t: 653.6, bg: B(v('la_avenue_night', {kb: 'out', from: 4, dim: 0.35})), fg: [{el: () => <IconGrid title="Siz tanlaysiz" color="green" items={[{label: 'Topshiriq bajarish', icon: 'target', at: 0.7}, {label: 'Shaharni tomosha', icon: 'eye', at: 3.0}, {label: 'Hikoyani davom', icon: 'book', at: 6.6}, {label: 'Yangi sarguzasht', icon: 'mount', at: 9.0}]} />}], fx: 'zoom', sfx: ['whoosh2']},
  {t: 665.0, bg: B(v('drift_country', {kb: 'in', from: 3})), fg: [K(['GTA’NI AJRATIB', 'TURADIGAN *JIHAT*'], {size: 110, color: 'green'})], fx: 'whip', sfx: ['car_by']},
  {t: 669.9, bg: B(im('dundee_city_quay.jpg', {kb: 'in', dim: 0.35})), fg: [K(['ENG', '*HAYRATLANARLISI*'], {size: 120})], fx: 'blur', sfx: ['riser_short']},
  {t: 673.7, bg: B(v('banknotes_falling', {kb: 'out', from: 2, grade: 'warm'})), fg: [K(['TEXNIK TAJRIBADAN', '*MILLIARDLAB $*'], {size: 110, color: 'green'})], fx: 'flash', sfx: ['coin']},
  {t: 681.9, bg: B(im('dma_team_2011.jpg', {kb: 'out', focus: '50% 40%'})), fg: [CO('Kichik studiya', 'dasturchilarning g‘oyasidan', {top: 250, color: 'cyan'})], fx: 'zoom', sfx: ['shutter']},
  {t: 686.9, bg: () => <Poll q="Sizningcha, eng zo‘r GTA qaysi?" options={[{text: 'Vice City', at: 5.8}, {text: 'San Andreas', at: 7.7}, {text: 'GTA 5', at: 9.4}, {text: 'GTA 6', at: 10.8}]} ctaAt={14.5} />, fx: 'flash', sfx: ['ding']},
  {t: 703.5, bg: B(v('fireworks_black', {kb: 'in', from: 3, dim: 0.2})), fg: [K(['YANGI DAVR', '*BOSHLANDI*'], {size: 140, until: 2.9}), {at: 2.9, el: () => <Kinetic lines={['TARIX HALI', '*TUGAMAGAN*']} size={130} top={700} color="pink" />}], fx: 'flash', sfx: ['impact_trailer']},
];

export const TOTAL_SEC = 709.06;
