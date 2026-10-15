/**
 * "Bitta kichkina narsa oldim" — Er-xotin va onlayn xarid dardi.
 *
 * Barcha vaqtlar src/data/timeline.json dan olinadi (tts/generate_audio.py
 * yaratadi), shuning uchun animatsiya ovozga avtomatik moslashadi:
 *  - har bir replika/pauza/sfx boshlanish va tugash vaqti
 *  - har bir replika uchun kadrma-kadr ovoz balandligi (lab-sinxron)
 *  - taglavha bo'laklari
 */
import {
  Circle,
  Line,
  Node,
  Rect,
  Txt,
  makeScene2D,
} from '@motion-canvas/2d';
import {
  Reference,
  SimpleSignal,
  ThreadGenerator,
  Vector2,
  all,
  chain,
  createComputed,
  createRef,
  createSignal,
  delay,
  easeInCubic,
  easeInOutCubic,
  easeInOutSine,
  easeOutBack,
  easeOutBounce,
  easeOutCubic,
  linear,
  sequence,
  spawn,
  tween,
  useRandom,
  useTime,
  waitFor,
} from '@motion-canvas/core';

import timeline from '../data/timeline.json';

// --------------------------------------------------------------------------- //
//  Timeline yordamchilari
// --------------------------------------------------------------------------- //
interface Sub {text: string; start: number; end: number}
interface Seg {
  id: string;
  type: string;
  start: number;
  end: number;
  speaker?: string;
  text?: string;
  env?: number[];
  subs?: Sub[];
}
const SEGS = timeline.segments as Seg[];
const T: Record<string, Seg> = Object.fromEntries(SEGS.map(s => [s.id, s]));
const SPEECH = SEGS.filter(s => s.type === 'speech');
const FPS = timeline.fps;

/** Berilgan qahramonning t vaqtdagi ovoz balandligi (0..1). */
function voiceLevel(speaker: string, t: number): number {
  for (const s of SPEECH) {
    if (s.speaker === speaker && t >= s.start && t < s.end) {
      const env = s.env!;
      return env[Math.min(env.length - 1, Math.floor((t - s.start) * FPS))];
    }
  }
  return 0;
}

/** Sahna vaqti `t` ga yetguncha kutish. */
function* until(t: number): ThreadGenerator {
  const dt = t - useTime();
  if (dt > 0) yield* waitFor(dt);
}

const FONT = 'Inter, DejaVu Sans, sans-serif';
const INK = '#1e1b2e';
const SKIN = '#ffd9b3';
const PURPLE = '#7b2ff7';

const SPEAKERS: Record<string, {name: string; color: string}> = {
  er: {name: 'ER', color: '#4fc3f7'},
  xotin: {name: 'XOTIN', color: '#f48fb1'},
  kuryer: {name: 'KURYER', color: '#ffb74d'},
};

/** Burchak (gradus): 0 = pastga, +90 = oldinga (+x). */
const polar = (len: number, deg: number) => {
  const r = (deg * Math.PI) / 180;
  return new Vector2(len * Math.sin(r), len * Math.cos(r));
};

// --------------------------------------------------------------------------- //
//  Stickman qahramon
// --------------------------------------------------------------------------- //
interface ManOptions {
  speaker: string;
  now: SimpleSignal<number>;
  shirt: string;
  x?: number;
  y?: number;
  scale?: number;
  kind?: 'er' | 'xotin' | 'kuryer';
}

function makeMan(o: ManOptions) {
  const root = createRef<Node>();
  const s = {
    hipY: createSignal(-135),
    lean: createSignal(0),
    armL1: createSignal(12), armL2: createSignal(4),
    armR1: createSignal(-12), armR2: createSignal(-4),
    legL1: createSignal(6), legL2: createSignal(2),
    legR1: createSignal(-6), legR2: createSignal(-2),
    gesture: createSignal(1),     // gapirganda qo'l harakati kuchi
    mouthExtra: createSignal(0),  // qo'shimcha og'iz ochilishi (qo'rquv)
    eyeSize: createSignal(1),
  };
  const level = createComputed(() => voiceLevel(o.speaker, o.now()));

  const hip = () => new Vector2(0, s.hipY());
  const shoulder = () => hip().add(polar(125, 180 + s.lean()));
  const neck = () => hip().add(polar(140, 180 + s.lean()));
  const head = () => hip().add(polar(185, 180 + s.lean()));
  const swing = (k: number) =>
    level() * 28 * s.gesture() * Math.sin(o.now() * 11 + k);
  const limb = (base: () => Vector2, a1: number, a2: number, l1 = 62, l2 = 58) => {
    const p1 = base();
    const p2 = p1.add(polar(l1, a1));
    return [p1, p2, p2.add(polar(l2, a2))];
  };
  const armL = () =>
    limb(shoulder, s.armL1() + swing(0), s.armL2() + swing(0) * 1.6);
  const armR = () =>
    limb(shoulder, s.armR1() - swing(1.7), s.armR2() - swing(1.7) * 1.6);
  const legL = () => limb(hip, s.legL1(), s.legL2(), 70, 68);
  const legR = () => limb(hip, s.legR1(), s.legR2(), 70, 68);

  const face = (dx: number, dy: number) => () => head().add([dx, dy]);
  const line = {stroke: INK, lineWidth: 11, lineCap: 'round' as const, lineJoin: 'round' as const};

  const node = (
    <Node ref={root} x={o.x ?? 0} y={o.y ?? 0} scale={o.scale ?? 1}>
      {/* oyoqlar */}
      <Line points={legL} {...line} />
      <Line points={legR} {...line} />
      {/* ko'ylak / tana */}
      {o.kind === 'xotin' ? (
        <Line
          points={() => {
            const sh = shoulder();
            const h = hip();
            return [sh.add([-14, 0]), sh.add([14, 0]), h.add([44, 30]), h.add([-44, 30])];
          }}
          closed
          fill={o.shirt}
          stroke={INK}
          lineWidth={5}
          lineJoin="round"
        />
      ) : (
        <Line points={() => [hip(), shoulder()]} stroke={o.shirt} lineWidth={44} lineCap="round" />
      )}
      <Line points={() => [hip(), neck()]} {...line} lineWidth={7} opacity={0.5} />
      {/* qo'llar */}
      <Line points={armL} {...line} />
      <Line points={armR} {...line} />
      <Circle position={() => armL()[2]} size={20} fill={SKIN} stroke={INK} lineWidth={4} />
      <Circle position={() => armR()[2]} size={20} fill={SKIN} stroke={INK} lineWidth={4} />
      {/* soch turmagi (xotin) */}
      {o.kind === 'xotin' && (
        <Circle position={face(-34, -34)} size={42} fill="#3b2314" />
      )}
      {/* bosh */}
      <Circle position={head} size={92} fill={SKIN} stroke={INK} lineWidth={7} />
      {o.kind === 'xotin' && (
        <Circle
          position={head}
          size={96}
          startAngle={185}
          endAngle={355}
          fill="#3b2314"
        />
      )}
      {o.kind === 'er' && (
        <Circle position={head} size={94} startAngle={200} endAngle={340} fill="#2b1d12" />
      )}
      {o.kind === 'kuryer' && (
        <Node position={head}>
          <Rect y={-34} width={92} height={34} radius={[40, 40, 4, 4]} fill={PURPLE} stroke={INK} lineWidth={5} />
          <Rect x={40} y={-20} width={46} height={10} radius={5} fill={PURPLE} stroke={INK} lineWidth={4} />
        </Node>
      )}
      {/* ko'zlar */}
      <Circle position={face(4, -6)} size={() => 11 * s.eyeSize()} fill={INK} />
      <Circle position={face(26, -6)} size={() => 11 * s.eyeSize()} fill={INK} />
      {/* og'iz — ovoz balandligiga qarab ochiladi */}
      <Rect
        position={face(18, 20)}
        width={() => 20 + level() * 6}
        height={() => 4 + level() * 22 + s.mouthExtra()}
        radius={12}
        fill="#6b1a1a"
        stroke={INK}
        lineWidth={3}
      />
      {o.kind === 'er' && (
        <Line points={() => [head().add([4, 8]), head().add([30, 8])]} stroke="#2b1d12" lineWidth={6} lineCap="round" opacity={0.85} />
      )}
    </Node>
  );

  /** Turgan holat. */
  function* stand(d = 0.4): ThreadGenerator {
    yield* all(
      s.hipY(-135, d), s.lean(0, d),
      s.legL1(6, d), s.legL2(2, d), s.legR1(-6, d), s.legR2(-2, d),
      s.armL1(12, d), s.armL2(4, d), s.armR1(-12, d), s.armR2(-4, d),
    );
  }

  /** x nuqtaga yurib borish. */
  function* walk(toX: number, d: number): ThreadGenerator {
    const fromX = root().x();
    yield* tween(d, v => {
      const p = v * d * 10;
      root().x(fromX + (toX - fromX) * easeInOutSine(v));
      const a = 26 * Math.sin(p);
      s.legL1(a); s.legL2(a - 14 * Math.max(0, -Math.cos(p)));
      s.legR1(-a); s.legR2(-a - 14 * Math.max(0, Math.cos(p)));
      s.armL1(-a * 0.8); s.armL2(-a * 0.8 + 10);
      s.armR1(a * 0.8); s.armR2(a * 0.8 + 10);
      s.hipY(-135 - 6 * Math.abs(Math.cos(p)));
    });
    yield* stand(0.2);
  }

  return {...s, root, node, level, stand, walk};
}

// --------------------------------------------------------------------------- //
//  Sahna
// --------------------------------------------------------------------------- //
export default makeScene2D(function* (view) {
  const now = createSignal(0);
  const rng = useRandom(2024);

  // Lab-sinxron uchun "soat": har kadrda sahna vaqtini yangilaydi.
  yield spawn(function* () {
    for (;;) {
      now(useTime());
      yield;
    }
  });

  view.fill('#000');

  // ======================= 1. XONA (ichkari) ============================== //
  const room = createRef<Node>();
  const door = createRef<Rect>();
  const doorWrap = createRef<Node>();
  const knockTxt = createRef<Txt>();
  const wifePeek = createRef<Node>();
  const tvScreen = createRef<Rect>();

  const husband = makeMan({speaker: 'er', now, shirt: '#3d8bd9', kind: 'er'});
  const wife = makeMan({speaker: 'xotin', now, shirt: '#e05a8a', kind: 'xotin'});
  const FLOOR = 330;

  view.add(
    <Node ref={room}>
      {/* devor va pol */}
      <Rect width={1920} height={1080} fill="#f3e4c8" />
      {Array.from({length: 13}, (_, i) => (
        <Rect x={-960 + i * 160} y={-100} width={6} height={860} fill="#e8d5b0" />
      ))}
      <Rect y={FLOOR + 210} width={1920} height={420} fill="#a8744a" />
      <Rect y={FLOOR + 4} width={1920} height={12} fill="#7a4f2e" />
      {/* oshxona eshigi (chapda) */}
      <Rect x={-760} y={FLOOR - 230} width={230} height={460} fill="#d9f0ef" stroke="#7a4f2e" lineWidth={14} clip>
        <Rect x={0} y={60} width={230} height={300} fill="#bfe3e0" />
        <Rect x={50} y={-120} width={70} height={90} fill="#ffffff" stroke="#9cc" lineWidth={4} />
        <Node ref={wifePeek} x={-200} y={230}>
          {wife.node}
        </Node>
      </Rect>
      <Rect x={-760} y={FLOOR - 500} width={200} height={50} radius={10} fill="#7a4f2e">
        <Txt text="OSHXONA" fontFamily={FONT} fontWeight={800} fontSize={30} fill="#fff" />
      </Rect>
      {/* televizor */}
      <Rect x={-420} y={FLOOR - 60} width={200} height={120} fill="#6b4a32" radius={8} />
      <Rect x={-420} y={FLOOR - 250} width={300} height={190} radius={14} fill="#222" />
      <Rect
        ref={tvScreen}
        x={-420}
        y={FLOOR - 250}
        width={262}
        height={154}
        radius={6}
        fill={() => ['#5fd3ff', '#9be15d', '#ffcf5c', '#ff7eb6'][Math.floor(now() * 1.6) % 4]}
      >
        <Txt
          text="GOL! 2:1"
          fontFamily={FONT}
          fontWeight={800}
          fontSize={44}
          fill="#1e1b2e"
          opacity={() => 0.6 + 0.4 * Math.sin(now() * 5)}
        />
      </Rect>
      {/* divan */}
      <Rect x={-30} y={FLOOR - 150} width={520} height={150} radius={40} fill="#c0392b" />
      <Rect x={-30} y={FLOOR - 60} width={560} height={110} radius={30} fill="#a93226" />
      <Rect x={-300} y={FLOOR - 90} width={70} height={170} radius={30} fill="#922b21" />
      <Rect x={240} y={FLOOR - 90} width={70} height={170} radius={30} fill="#922b21" />
      <Node x={60} y={FLOOR - 40} scale={[-1, 1]} zIndex={10}>
        {husband.node}
      </Node>
      {/* kirish eshigi (o'ngda) */}
      <Rect x={680} y={FLOOR - 230} width={260} height={480} fill="#2b2b2b" clip>
        {/* eshik orqasidagi ulkan fura (ko'rinib turgan qismi) */}
        <Rect width={260} height={480} fill="#87ceeb" />
        <Rect y={40} width={600} height={600} fill="#eeeeee" stroke="#555" lineWidth={8}>
          {Array.from({length: 6}, (_, i) => (
            <Rect y={-230 + i * 34} width={600} height={14} fill="#999" />
          ))}
          <Circle x={-95} y={70} size={80} fill="#fff59d" stroke="#555" lineWidth={6} />
          <Circle x={95} y={70} size={80} fill="#fff59d" stroke="#555" lineWidth={6} />
        </Rect>
      </Rect>
      <Node ref={doorWrap} x={810} y={FLOOR - 230}>
        <Rect ref={door} offset={[1, 0]} width={260} height={480} fill="#8e5b34" stroke="#5e3a1f" lineWidth={10}>
          <Rect x={0} y={-110} width={180} height={150} stroke="#5e3a1f" lineWidth={8} radius={6} />
          <Rect x={0} y={100} width={180} height={150} stroke="#5e3a1f" lineWidth={8} radius={6} />
          <Circle x={-95} y={10} size={26} fill="#f1c40f" />
        </Rect>
      </Node>
      <Rect x={680} y={FLOOR - 230} width={280} height={500} stroke="#5e3a1f" lineWidth={16} />
      <Txt
        ref={knockTxt}
        x={540}
        y={FLOOR - 470}
        text="TAQ-TAQ!"
        fontFamily={FONT}
        fontWeight={900}
        fontSize={78}
        fill="#e74c3c"
        stroke="#fff"
        lineWidth={8}
        strokeFirst
        rotation={-8}
        scale={0}
      />
    </Node>,
  );

  // Er divanda chalqancha yotibdi (yarim yotgan holat).
  husband.hipY(-60);
  husband.lean(35);
  husband.legL1(80); husband.legL2(70);
  husband.legR1(86); husband.legR2(78);
  husband.armL1(-150); husband.armL2(110); // qo'li boshi ortida
  husband.armR1(60); husband.armR2(90);    // pult bilan TV ga
  wife.armR1(-120); wife.armR2(-150);

  // ======================= 2. KO'CHA (tashqari) =========================== //
  const outside = createRef<Node>();
  const truck = createRef<Node>();
  const doorL = createRef<Rect>();
  const doorR = createRef<Rect>();
  const boxesLayer = createRef<Node>();
  const hand = createRef<Node>();
  const handWave = createSignal(0);
  const courierWrap = createRef<Node>();
  const listPaper = createRef<Rect>();
  const wallet = createRef<Node>();
  const wingL = createRef<Node>();
  const wingR = createRef<Node>();
  const halo = createRef<Circle>();
  const scream = createRef<Node>();
  const pile = createRef<Node>();
  const GROUND = 390;

  const husband2 = makeMan({speaker: 'er', now, shirt: '#3d8bd9', kind: 'er'});
  const courier = makeMan({speaker: 'kuryer', now, shirt: PURPLE, kind: 'kuryer'});

  const box = (w: number, h: number) => (
    <Rect width={w} height={h} fill="#d9a066" stroke="#8a5a2b" lineWidth={5} radius={4}>
      <Rect width={w * 0.18} height={h} fill="#f3d19c" opacity={0.9} />
      <Rect width={w * 0.5} height={h * 0.32} y={h * 0.18} radius={4} fill={PURPLE}>
        <Txt text="UZUM" fontFamily={FONT} fontWeight={900} fontSize={h * 0.2} fill="#fff" />
      </Rect>
    </Rect>
  );

  view.add(
    <Node ref={outside} opacity={0}>
      <Rect width={1920} height={1080} fill="#8fd3ff" />
      <Circle x={-720} y={-380} size={160} fill="#fff176" />
      <Rect y={GROUND + 170} width={1920} height={340} fill="#7f8c8d" />
      <Rect y={GROUND + 4} width={1920} height={10} fill="#566573" />
      {/* uy eshigi (chap chekka) */}
      <Rect x={-860} y={GROUND - 260} width={260} height={540} fill="#f3e4c8" stroke="#7a4f2e" lineWidth={14} />
      {/* ulkan fura (orqa tomondan) */}
      <Node ref={truck} x={120} y={45} scale={0.88}>
        <Rect y={-120} width={1320} height={880} fill="#ecf0f1" stroke="#34495e" lineWidth={14} radius={10} />
        <Txt y={-520} text="ONLAYN XARID EKSPRESS" fontFamily={FONT} fontWeight={900} fontSize={64} fill={PURPLE} />
        <Rect y={-80} width={1180} height={740} fill="#3b3b3b" clip>
          {/* fura ichidagi cheksiz qutilar devori */}
          {Array.from({length: 11 * 8}, (_, i) => {
            const c = i % 11;
            const r = Math.floor(i / 11);
            return (
              <Node x={-540 + c * 108} y={-320 + r * 92} rotation={(c * 7 + r * 3) % 5 - 2}>
                {box(104, 88)}
              </Node>
            );
          })}
        </Rect>
        <Rect ref={doorL} x={-590} y={-80} offset={[-1, 0]} width={590} height={740} fill="#bdc3c7" stroke="#34495e" lineWidth={10}>
          <Rect x={295} width={14} height={740} fill="#7f8c8d" />
        </Rect>
        <Rect ref={doorR} x={590} y={-80} offset={[1, 0]} width={590} height={740} fill="#bdc3c7" stroke="#34495e" lineWidth={10}>
          <Rect x={-295} width={14} height={740} fill="#7f8c8d" />
        </Rect>
        {[-480, -330, 330, 480].map(x => (
          <Circle x={x} y={300} size={150} fill="#2c3e50" stroke="#111" lineWidth={10}>
            <Circle size={60} fill="#95a5a6" />
          </Circle>
        ))}
      </Node>
      <Node x={-200} y={GROUND}>
        {husband2.node}
      </Node>
      <Node ref={pile} />
      <Node ref={boxesLayer} />
      {/* chiqib turgan qo'l */}
      <Node ref={hand} x={-215} y={GROUND - 600} opacity={0} rotation={() => -12 + handWave() * 18}>
        <Line points={[[0, 120], [0, 0]]} stroke={INK} lineWidth={12} lineCap="round" />
        <Line points={[[-14, 0], [-20, -32]]} stroke={INK} lineWidth={7} lineCap="round" />
        <Line points={[[0, -4], [0, -40]]} stroke={INK} lineWidth={7} lineCap="round" />
        <Line points={[[14, 0], [20, -32]]} stroke={INK} lineWidth={7} lineCap="round" />
        <Circle size={32} fill={SKIN} stroke={INK} lineWidth={4} />
      </Node>
      {/* hamyon */}
      <Node ref={wallet} x={-170} y={GROUND - 650} scale={0}>
        <Node ref={wingL} x={-60} y={-10} scale={0}>
          <Line
            points={[[0, 0], [-90, -80], [-150, -40], [-120, 0], [-150, 30], [-60, 40]]}
            closed
            fill="#ffffff"
            stroke="#9ab"
            lineWidth={5}
            lineJoin="round"
            offset={[1, 0]}
          />
        </Node>
        <Node ref={wingR} x={60} y={-10} scale={0}>
          <Line
            points={[[0, 0], [90, -80], [150, -40], [120, 0], [150, 30], [60, 40]]}
            closed
            fill="#ffffff"
            stroke="#9ab"
            lineWidth={5}
            lineJoin="round"
            offset={[-1, 0]}
          />
        </Node>
        <Circle ref={halo} y={-95} width={110} height={30} stroke="#f1c40f" lineWidth={10} opacity={0} />
        <Rect width={150} height={100} radius={16} fill="#8e5b34" stroke="#4a2e17" lineWidth={6}>
          <Rect x={40} y={0} width={70} height={46} radius={10} fill="#a86d3e" stroke="#4a2e17" lineWidth={4} />
          {/* yig'layotgan yuz */}
          <Line points={[[-50, -18], [-30, -12]]} stroke={INK} lineWidth={6} lineCap="round" />
          <Line points={[[-10, -12], [10, -18]]} stroke={INK} lineWidth={6} lineCap="round" />
          <Line points={[[-40, 26], [-20, 14], [0, 26]]} stroke={INK} lineWidth={6} lineCap="round" />
          {[-40, 0].map((x, i) => (
            <Circle
              x={x}
              y={() => -5 + ((now() * 120 + i * 30) % 70)}
              size={14}
              fill="#4fc3f7"
              opacity={() => 1 - ((now() * 120 + i * 30) % 70) / 70}
            />
          ))}
        </Rect>
      </Node>
      {/* kuryer */}
      <Node ref={courierWrap} x={1150} y={GROUND} scale={[-1, 1]}>
        {courier.node}
        <Rect
          ref={listPaper}
          x={() => courier.root().x() + 100}
          y={-262}
          width={90}
          height={0}
          offset={[0, -1]}
          fill="#ffffff"
          stroke="#bbb"
          lineWidth={3}
          clip
        >
          {Array.from({length: 40}, (_, i) => (
            <Rect y={20 + i * 26} offset={[0, -1]} width={66} height={5} fill="#90a4ae" />
          ))}
        </Rect>
      </Node>
      <Node ref={scream} x={-150} y={GROUND - 520} scale={0}>
        <Line
          points={Array.from({length: 24}, (_, i) => polar(i % 2 ? 250 : 180, i * 15).mul([1.4, 0.75]))}
          closed
          fill="#fff"
          stroke="#e74c3c"
          lineWidth={10}
        />
        <Txt text="NIYEEEEET!" fontFamily={FONT} fontWeight={900} fontSize={84} fill="#e74c3c" />
      </Node>
    </Node>,
  );
  courier.armL1(70); courier.armL2(120);

  // ======================= 3. TITUL KARTA ================================= //
  const title = createRef<Node>();
  const titleTxt = createRef<Txt>();
  const subTxt = createRef<Txt>();
  const endCard = createRef<Node>();
  view.add(
    <Node ref={title}>
      <Rect width={1920} height={1080} fill={PURPLE} />
      {Array.from({length: 14}, (_, i) => (
        <Node
          x={-880 + i * 135}
          y={() => -620 + ((now() * 260 + i * 97) % 1300)}
          rotation={() => now() * 40 + i * 25}
          opacity={0.25}
        >
          {box(90, 76)}
        </Node>
      ))}
      <Txt ref={titleTxt} y={-40} text={timeline.title} fontFamily={FONT} fontWeight={900} fontSize={110} fill="#fff" scale={0} />
      <Txt ref={subTxt} y={80} text={timeline.subtitle} fontFamily={FONT} fontWeight={600} fontSize={52} fill="#ffe082" opacity={0} />
    </Node>,
  );

  // ======================= 4. TAGLAVHALAR ================================ //
  const subBar = createRef<Rect>();
  const subWords = createRef<Rect>();
  const subName = createRef<Txt>();
  const subTag = createRef<Rect>();
  view.add(
    <Rect
      ref={subBar}
      y={430}
      layout
      direction="column"
      alignItems="center"
      gap={12}
      padding={[20, 44]}
      radius={28}
      fill="rgba(20,16,40,0.82)"
      opacity={0}
    >
      <Rect ref={subTag} layout padding={[4, 18]} radius={14} fill="#4fc3f7">
        <Txt ref={subName} text="ER" fontFamily={FONT} fontWeight={900} fontSize={30} fill={INK} />
      </Rect>
      <Rect ref={subWords} layout wrap="wrap" justifyContent="center" maxWidth={1500} gap={14} />
    </Rect>,
  );

  function* subtitles(): ThreadGenerator {
    const chunks = SPEECH.flatMap(s => s.subs!.map(c => ({...c, speaker: s.speaker!})));
    for (let i = 0; i < chunks.length; i++) {
      const c = chunks[i];
      const next = chunks[i + 1];
      yield* until(c.start - 0.08);
      const sp = SPEAKERS[c.speaker];
      subName().text(sp.name);
      subTag().fill(sp.color);
      subWords().removeChildren();
      const words = c.text.split(/\s+/).map(w => (
        <Txt text={w} fontFamily={FONT} fontWeight={700} fontSize={50} fill="#fff" opacity={0} scale={0.6} />
      )) as Txt[];
      subWords().add(words);
      if (subBar().opacity() < 1) yield* subBar().opacity(1, 0.15);
      const span = Math.max(0.3, (c.end - c.start) * 0.75);
      yield* sequence(
        span / words.length,
        ...words.map(w => all(w.opacity(1, 0.18), w.scale(1, 0.25, easeOutBack))),
      );
      yield* until(c.end);
      if (!next || next.start - c.end > 0.35) yield* subBar().opacity(0, 0.25);
    }
  }
  yield spawn(subtitles);

  // ======================= 5. SSENARIY ==================================== //
  // --- Titul ---
  yield* all(titleTxt().scale(1, 0.8, easeOutBack), delay(0.4, subTxt().opacity(1, 0.6)));
  yield* until(T.intro.end - 0.6);
  yield* all(title().opacity(0, 0.6), title().scale(1.15, 0.6));
  title().remove();

  // --- Eshik taqillaydi ---
  const knockAt = [0, 0.28, 0.56, 1.0, 1.22];
  yield spawn(knockTxt().scale(1, 0.25, easeOutBack));
  for (const k of knockAt) {
    yield* until(T.knock.start + k);
    yield* chain(doorWrap().x(818, 0.04), doorWrap().x(804, 0.05), doorWrap().x(810, 0.04));
  }
  yield* knockTxt().scale(0, 0.2);

  // --- Er: "Xotiiin, eshikni och! Kim u?" ---
  yield* until(T.er1.start);
  yield* all(husband.lean(5, 0.3), husband.armR1(150, 0.3), husband.armR2(170, 0.3));
  yield* until(T.er1.end - 0.3);
  yield* all(husband.lean(35, 0.4), husband.armR1(60, 0.4), husband.armR2(90, 0.4));

  // --- Xotin oshxonadan ---
  yield* until(T.xotin1.start - 0.45);
  yield* wifePeek().x(-30, 0.45, easeOutBack);
  yield* until(T.xotin1.end);
  yield* wifePeek().x(-200, 0.4, easeInCubic);

  // --- Er: "Xo'p." — o'rnidan turib eshik tomon boradi ---
  yield* until(T.er2.start);
  const hWrap = husband.root().parent()!;
  yield* all(
    husband.stand(0.5),
    hWrap.y(FLOOR, 0.5),
  );
  hWrap.scale([1, 1]);
  yield* husband.walk(530 - hWrap.x(), Math.max(0.8, T.walk.end - useTime() - 0.9));
  yield* all(husband.armR1(110, 0.25), husband.armR2(100, 0.25));
  // eshik ochiladi — orqasida ulkan fura!
  yield* door().scale.x(0.12, 0.45, easeOutCubic);
  yield* all(husband.eyeSize(2, 0.25), husband.mouthExtra(18, 0.25), husband.armR1(160, 0.25), husband.armL1(-160, 0.25));

  // --- Fura signali: ko'chaga o'tamiz ---
  yield* until(T.truck.start);
  yield* all(
    room().scale(3.2, 0.7, easeInCubic),
    room().position([-680 * 3.2, -(FLOOR - 230) * 3.2], 0.7, easeInCubic),
    outside().opacity(1, 0.7, easeInCubic),
  );
  room().remove();
  husband2.eyeSize(2);
  husband2.mouthExtra(18);
  husband2.armL1(150); husband2.armL2(170);
  husband2.armR1(-150); husband2.armR2(-170);
  yield* all(
    doorL().scale.x(0.05, 0.6, easeOutCubic),
    doorR().scale.x(0.05, 0.6, easeOutCubic),
  );

  // --- Qutilar ko'chkisi ---
  yield* until(T.avalanche.start);
  const pileBoxes: ThreadGenerator[] = [];
  const rows = [9, 8, 7, 6, 5, 4, 3];
  let n = 0;
  rows.forEach((count, r) => {
    for (let c = 0; c < count; c++) {
      const tx = -200 + (c - (count - 1) / 2) * 112 + rng.nextFloat(-14, 14);
      const ty = GROUND - 46 - r * 86;
      const sx = 120 + rng.nextFloat(-520, 520);
      const sy = rng.nextFloat(-420, 120);
      const b = (
        <Node x={sx} y={sy} rotation={rng.nextFloat(-40, 40)} scale={0.9}>
          {box(108, 90)}
        </Node>
      ) as Node;
      pile().add(b);
      const d = 0.45 + rng.nextFloat(0, 0.25);
      pileBoxes.push(
        delay(
          n * 0.045,
          all(
            b.x(tx, d, linear),
            b.y(ty, d, easeOutBounce),
            b.rotation(rng.nextFloat(-10, 10), d),
            b.scale(1, d),
          ),
        ),
      );
      n++;
    }
  });
  // ekrandan tashqariga uchib ketayotgan ortiqcha qutilar
  const flyers = Array.from({length: 22}, () => {
    const b = (
      <Node x={120 + rng.nextFloat(-500, 500)} y={rng.nextFloat(-400, 100)} rotation={rng.nextFloat(-30, 30)}>
        {box(108, 90)}
      </Node>
    ) as Node;
    boxesLayer().add(b);
    const d = 0.9 + rng.nextFloat(0, 0.5);
    return delay(
      rng.nextFloat(0, 2.2),
      all(
        b.x(b.x() + rng.nextFloat(-1300, 1300), d, linear),
        b.y(900, d, easeInCubic),
        b.rotation(rng.nextFloat(-360, 360), d),
      ),
    );
  });
  const shake = tween(2.6, v => {
    const a = 14 * (1 - v);
    outside().position([rng.nextFloat(-a, a), rng.nextFloat(-a, a)]);
  });
  yield* all(
    ...pileBoxes,
    ...flyers,
    shake,
    delay(0.5, husband2.root().opacity(0, 0.4)),
    delay(1.4, hand().opacity(1, 0.3)),
  );
  outside().position([0, 0]);
  boxesLayer().removeChildren();
  yield spawn(
    tween(30, v => handWave(Math.sin(v * 30 * 4) * 0.6)),
  );

  // --- Kuryer uzun ro'yxat bilan ---
  yield* until(T.kuryer1.start - 1.2);
  yield* courier.walk(500, 1.1); // o'rami teskari (scale -1): ekranda chapga yuradi
  yield* all(
    listPaper().height(900, 1.6, easeOutBounce),
    courier.armL1(70, 0.4),
    courier.armL2(120, 0.4),
    courier.armR1(80, 0.4),
    courier.armR2(110, 0.4),
  );

  // --- Hamyon farishta bo'lib uchib ketadi ---
  yield* until(T.wallet.start);
  yield* wallet().scale(1.4, 0.5, easeOutBack);
  yield* all(wingL().scale(1, 0.6, easeOutBack), wingR().scale(1, 0.6, easeOutBack), halo().opacity(1, 0.6));
  yield spawn(
    tween(8, v => {
      const f = 1 - 0.35 * Math.abs(Math.sin(v * 8 * 9));
      wingL().scale.y(f);
      wingR().scale.y(f);
    }),
  );
  yield* all(
    wallet().y(-700, T.wallet.end - useTime() - 0.1, easeInCubic),
    wallet().x(-60, T.wallet.end - useTime() - 0.1, easeInOutSine),
  );

  // --- "Niyeeeet!" ---
  yield* until(T.er3.start);
  yield spawn(
    tween(T.er3.end - T.er3.start + 0.3, v => {
      pile().position([Math.sin(v * 90) * 10 * (1 - v), Math.cos(v * 70) * 6 * (1 - v)]);
    }),
  );
  yield* scream().scale(1, 0.35, easeOutBack);
  yield* until(T.er3.end + 0.3);
  yield* scream().scale(0, 0.3);

  // --- Yakuniy karta ---
  view.add(
    <Node ref={endCard} opacity={0}>
      <Rect width={1920} height={1080} fill={PURPLE} />
      <Txt y={-60} text={timeline.title} fontFamily={FONT} fontWeight={900} fontSize={100} fill="#fff" />
      <Txt y={60} text="...davomi bor: yana 2 ta fura yo'lda!" fontFamily={FONT} fontWeight={600} fontSize={52} fill="#ffe082" />
    </Node>,
  );
  yield* until(T.outro.start + 0.2);
  yield* endCard().opacity(1, 0.6);
  yield* until(timeline.duration);
});
