// Yo'l belgilarining sxematik SVG tasvirlari (Vena konvensiyasi uslubida).
// Rasmiy ko'rinish — YHQ 1-ilovasida. Bu tasvirlar o'quv maqsadida soddalashtirilgan.
import { cn } from "@/lib/utils";

const RED = "#d32027";
const BLUE = "#1f5fbf";
const YELLOW = "#f6c400";
const BLACK = "#1a1a1a";
const WHITE = "#ffffff";

type P = { c: string };

// ───── Piktogrammalar (markazi ~50,55; o'lchami ~40) ─────
const pict: Record<string, (p: P) => React.ReactNode> = {
  arrowUp: ({ c }) => <path d="M50 22 L66 42 H56 V78 H44 V42 H34 Z" fill={c} />,
  arrowRight: ({ c }) => <path d="M78 50 L58 34 V44 H22 V56 H58 V66 Z" fill={c} />,
  arrowLeft: ({ c }) => <path d="M22 50 L42 34 V44 H78 V56 H42 V66 Z" fill={c} />,
  arrowUpRight: ({ c }) => (
    <g fill={c}>
      <path d="M40 80 V44 L30 44 L44 24 L58 44 H48 V80 Z" />
      <path d="M48 62 Q48 50 60 50 H66 V42 L80 54 L66 66 V58 H60 Q56 58 56 62 V80 H48 Z" />
    </g>
  ),
  uTurn: ({ c }) => <path d="M60 80 V42 Q60 28 46 28 Q32 28 32 42 V56 H24 L36 72 L48 56 H40 V42 Q40 36 46 36 Q52 36 52 42 V80 Z" fill={c} />,
  roundabout: ({ c }) => (
    <g fill="none" stroke={c} strokeWidth="7">
      <path d="M50 26 A24 24 0 0 1 72 42" /><path d="M74 58 A24 24 0 0 1 54 74" /><path d="M38 72 A24 24 0 0 1 27 46" />
      <path d="M72 42 l-1 -12 M72 42 l-11 -2" strokeWidth="5" /><path d="M54 74 l10 6 M54 74 l7 -9" strokeWidth="5" /><path d="M27 46 l-4 11 M27 46 l10 -5" strokeWidth="5" />
    </g>
  ),
  car: ({ c }) => (
    <g fill={c}>
      <path d="M28 60 L32 46 Q34 40 40 40 H60 Q66 40 68 46 L72 60 V70 H28 Z" />
      <circle cx="37" cy="71" r="5" /><circle cx="63" cy="71" r="5" />
    </g>
  ),
  car2: ({ c }) => (
    <g>
      <g fill={RED} transform="translate(-14 0) scale(0.85) translate(9 10)"><path d="M28 60 L32 46 Q34 40 40 40 H60 Q66 40 68 46 L72 60 V70 H28 Z" /><circle cx="37" cy="71" r="5" /><circle cx="63" cy="71" r="5" /></g>
      <g fill={c} transform="translate(14 0) scale(0.85) translate(9 10)"><path d="M28 60 L32 46 Q34 40 40 40 H60 Q66 40 68 46 L72 60 V70 H28 Z" /><circle cx="37" cy="71" r="5" /><circle cx="63" cy="71" r="5" /></g>
    </g>
  ),
  truck: ({ c }) => (
    <g fill={c}>
      <rect x="24" y="36" width="34" height="28" rx="2" /><path d="M60 46 H70 L78 56 V64 H60 Z" />
      <circle cx="34" cy="68" r="5" /><circle cx="68" cy="68" r="5" />
    </g>
  ),
  bus: ({ c }) => (
    <g fill={c}>
      <rect x="26" y="30" width="48" height="38" rx="5" /><rect x="31" y="35" width="38" height="14" fill={WHITE} opacity=".9" />
      <circle cx="36" cy="70" r="4" /><circle cx="64" cy="70" r="4" />
    </g>
  ),
  ped: ({ c }) => (
    <g fill={c}>
      <circle cx="52" cy="26" r="6" />
      <path d="M48 34 L58 34 L62 52 L56 54 L54 46 L52 58 L60 78 L53 80 L46 64 L42 80 L35 78 L42 56 L44 44 L38 54 L33 51 Z" />
    </g>
  ),
  children: ({ c }) => (
    <g fill={c}>
      <circle cx="40" cy="30" r="6" /><path d="M36 38 H45 L48 58 L52 78 H45 L41 62 L38 78 H31 L34 58 Z" />
      <circle cx="62" cy="40" r="5" /><path d="M58 47 H66 L68 62 L71 78 H65 L62 66 L60 78 H54 L57 62 Z" />
    </g>
  ),
  bike: ({ c }) => (
    <g fill="none" stroke={c} strokeWidth="4.5">
      <circle cx="32" cy="62" r="11" /><circle cx="68" cy="62" r="11" />
      <path d="M32 62 L44 42 H60 L68 62 M44 42 L52 62 L60 42 M40 36 H48 M58 38 L62 34" />
    </g>
  ),
  train: ({ c }) => (
    <g fill={c}>
      <rect x="26" y="40" width="40" height="22" /><rect x="52" y="30" width="14" height="12" /><rect x="30" y="32" width="8" height="10" />
      <path d="M66 46 H74 L76 62 H66 Z" />
      <circle cx="34" cy="66" r="5" /><circle cx="48" cy="66" r="5" /><circle cx="62" cy="66" r="5" />
    </g>
  ),
  fence: ({ c }) => (
    <g fill={c}>
      <rect x="22" y="40" width="56" height="7" /><rect x="22" y="58" width="56" height="7" />
      {[26, 38, 50, 62, 72].map((x) => <rect key={x} x={x} y="32" width="5" height="44" />)}
    </g>
  ),
  tram: ({ c }) => (
    <g fill={c}>
      <path d="M50 22 L44 30 M50 22 L56 30" stroke={c} strokeWidth="3" />
      <rect x="32" y="30" width="36" height="40" rx="6" /><rect x="37" y="36" width="26" height="14" fill={WHITE} />
      <rect x="34" y="72" width="8" height="5" /><rect x="58" y="72" width="8" height="5" />
    </g>
  ),
  cross: ({ c }) => <path d="M45 24 H55 V48 H78 V58 H55 V82 H45 V58 H22 V48 H45 Z" fill={c} />,
  crossMain: ({ c }) => <g fill={c}><path d="M44 22 H56 V82 H44 Z" /><path d="M24 50 H76 V56 H24 Z" /></g>,
  light: () => (
    <g>
      <rect x="40" y="26" width="20" height="52" rx="4" fill={BLACK} />
      <circle cx="50" cy="35" r="5.5" fill={RED} /><circle cx="50" cy="52" r="5.5" fill={YELLOW} /><circle cx="50" cy="69" r="5.5" fill="#1aa64a" />
    </g>
  ),
  curveR: ({ c }) => <path d="M40 82 V56 Q40 40 56 36 V28 L72 40 L56 52 V44 Q50 46 50 56 V82 Z" fill={c} />,
  curveL: ({ c }) => <path d="M60 82 V56 Q60 40 44 36 V28 L28 40 L44 52 V44 Q50 46 50 56 V82 Z" fill={c} />,
  slopeDown: ({ c }) => (
    <g fill={c}><path d="M20 44 L80 78 H20 Z" /><text x="56" y="48" fontSize="16" fontWeight="700" fontFamily="Arial">10%</text></g>
  ),
  slopeUp: ({ c }) => (
    <g fill={c}><path d="M80 44 L20 78 H80 Z" /><text x="22" y="48" fontSize="16" fontWeight="700" fontFamily="Arial">10%</text></g>
  ),
  slippery: ({ c }) => (
    <g>
      <g fill={c}><path d="M36 46 L39 38 Q40 34 44 34 H58 Q62 34 63 38 L66 46 V52 H36 Z" /><circle cx="42" cy="53" r="3.5" /><circle cx="60" cy="53" r="3.5" /></g>
      <path d="M34 80 Q42 70 38 62 M50 80 Q58 70 54 62 M66 80 Q74 70 70 62" fill="none" stroke={c} strokeWidth="4" />
    </g>
  ),
  bumps: ({ c }) => <path d="M18 74 Q28 56 38 74 Q48 56 58 74 Q68 56 78 74 V80 H18 Z" fill={c} />,
  hump: ({ c }) => <path d="M18 76 H32 Q50 46 68 76 H82 V80 H18 Z" fill={c} />,
  narrow: ({ c }) => <g fill={c}><path d="M34 80 V60 L42 44 V22 H36 V44 L28 60 V80 Z" /><path d="M66 80 V60 L58 44 V22 H64 V44 L72 60 V80 Z" /></g>,
  twoWay: ({ c }) => (
    <g fill={c}><path d="M38 22 L50 36 H42 V80 H34 V36 H26 Z" /><path d="M62 80 L50 66 H58 V24 H66 V66 H74 Z" /></g>
  ),
  works: ({ c }) => (
    <g fill={c}>
      <circle cx="44" cy="30" r="6" /><path d="M40 38 L52 40 L56 56 L64 74 L57 77 L50 62 L44 66 L40 78 L33 76 L38 60 Z" />
      <path d="M54 44 L74 30 L76 34 L58 48 Z" /><path d="M66 70 L82 78 H62 Z" />
    </g>
  ),
  cow: ({ c }) => (
    <g fill={c}>
      <path d="M26 46 Q26 38 34 38 H66 L72 34 L76 38 L74 48 Q72 54 66 54 V74 H60 V60 H40 V74 H34 V56 Q26 54 26 46 Z" />
    </g>
  ),
  deer: ({ c }) => (
    <g fill={c}>
      <path d="M30 52 Q32 46 40 46 H60 L66 36 L64 28 L70 34 L72 26 L74 36 L70 46 L72 52 L66 54 V76 H61 V62 H42 V76 H37 V60 Q30 58 30 52 Z" />
    </g>
  ),
  rocks: ({ c }) => (
    <g fill={c}><path d="M24 80 L24 26 L40 38 Z" /><circle cx="52" cy="46" r="6" /><circle cx="62" cy="62" r="7" /><circle cx="48" cy="72" r="6" /></g>
  ),
  excl: ({ c }) => <g fill={c}><rect x="45" y="28" width="10" height="34" rx="3" /><circle cx="50" cy="72" r="6" /></g>,
  horn: ({ c }) => <path d="M24 44 H38 L66 28 V76 L38 60 H24 Z" fill={c} />,
  pLetter: ({ c }) => <text x="50" y="72" textAnchor="middle" fontSize="58" fontWeight="800" fontFamily="Arial" fill={c}>P</text>,
  motorway: ({ c }) => (
    <g fill={c}><path d="M18 40 H82 V48 H18 Z" /><path d="M30 48 L22 82 H34 L40 48 Z" /><path d="M70 48 L78 82 H66 L60 48 Z" /><path d="M48 52 H52 V60 H48 Z M48 66 H52 V78 H48 Z" /></g>
  ),
  house: ({ c }) => (
    <g fill={c}>
      <path d="M22 50 L42 32 L62 50 V76 H22 Z" /><rect x="36" y="58" width="12" height="18" fill={BLUE} />
      <circle cx="70" cy="44" r="5" /><path d="M66 52 H74 L76 76 H70 L69 64 L67 76 H62 Z" />
      <circle cx="30" cy="80" r="2.5" /><circle cx="60" cy="80" r="2.5" />
    </g>
  ),
  medical: () => <path d="M44 28 H56 V44 H72 V56 H56 V72 H44 V56 H28 V44 H44 Z" fill={RED} />,
  fuel: () => (
    <g fill={BLACK}><rect x="32" y="30" width="26" height="44" rx="2" /><rect x="36" y="34" width="18" height="12" fill={WHITE} /><path d="M58 40 H64 L70 48 V68 Q70 72 66 72 Q62 72 62 68 V56 H58 V52 H66 V68 V48 L62 44 H58 Z" /></g>
  ),
  rest: () => (
    <g fill={BLACK}><path d="M50 22 L66 48 H58 L70 64 H54 V76 H46 V64 H30 L42 48 H34 Z" /></g>
  ),
  stopline: ({ c }) => (
    <g fill={c}><rect x="22" y="58" width="56" height="8" /><path d="M46 22 H54 V46 H62 L50 56 L38 46 H46 Z" /></g>
  ),
  busLane: ({ c }) => (
    <g fill={c}><path d="M50 18 L60 30 H54 V40 H46 V30 H40 Z" /><rect x="34" y="44" width="32" height="28" rx="4" /><rect x="37" y="48" width="26" height="10" fill={BLUE} /><circle cx="40" cy="74" r="3" /><circle cx="60" cy="74" r="3" /></g>
  ),
  pedCross: () => (
    <g>
      <path d="M50 18 L84 80 H16 Z" fill={WHITE} />
      <g fill={BLACK} transform="translate(16 26) scale(0.68)"><circle cx="52" cy="26" r="6" /><path d="M48 34 L58 34 L62 52 L56 54 L54 46 L52 58 L60 78 L53 80 L46 64 L42 80 L35 78 L42 56 L44 44 L38 54 L33 51 Z" /></g>
      <g fill={BLACK}>{[22, 36, 50, 64].map((x) => <rect key={x} x={x} y="73" width="8" height="5" />)}</g>
    </g>
  ),
};

function Num({ n, c, size = 40 }: { n: string; c: string; size?: number }) {
  return <text x="50" y="50" dy="0.36em" textAnchor="middle" fontSize={size} fontWeight="800" fontFamily="Arial, sans-serif" fill={c}>{n}</text>;
}

// ───── Belgi shakllari ─────
function Warning({ children }: { children: React.ReactNode }) {
  return (
    <>
      <path d="M50 6 L96 88 Q97 92 92 92 H8 Q3 92 4 88 Z" fill={RED} />
      <path d="M50 20 L84 82 H16 Z" fill={WHITE} />
      <g transform="translate(17 30) scale(0.66)">{children}</g>
    </>
  );
}
function RoundProhib({ children, fill = WHITE }: { children?: React.ReactNode; fill?: string }) {
  return (
    <>
      <circle cx="50" cy="50" r="46" fill={RED} />
      <circle cx="50" cy="50" r="36" fill={fill} />
      {children && <g transform="translate(14 14) scale(0.72)">{children}</g>}
    </>
  );
}
function EndOf({ children }: { children?: React.ReactNode }) {
  return (
    <>
      <circle cx="50" cy="50" r="46" fill={WHITE} stroke="#666" strokeWidth="2" />
      {children && <g opacity="0.55" transform="translate(14 14) scale(0.72)">{children}</g>}
      <g stroke="#333" strokeWidth="3">{[-12, -4, 4, 12].map((o) => <line key={o} x1={22 + o} y1={78 + o} x2={78 + o} y2={22 + o} />)}</g>
    </>
  );
}
function Mandatory({ children }: { children: React.ReactNode }) {
  return (
    <>
      <circle cx="50" cy="50" r="46" fill={BLUE} />
      <circle cx="50" cy="50" r="43" fill="none" stroke={WHITE} strokeWidth="2" />
      <g transform="translate(10 8) scale(0.8)">{children}</g>
    </>
  );
}
function Info({ children, bg = BLUE }: { children: React.ReactNode; bg?: string }) {
  return (
    <>
      <rect x="6" y="6" width="88" height="88" rx="9" fill={bg} />
      <rect x="10" y="10" width="80" height="80" rx="6" fill="none" stroke={WHITE} strokeWidth="2" />
      <g transform="translate(10 8) scale(0.8)">{children}</g>
    </>
  );
}
function Service({ children }: { children: React.ReactNode }) {
  return (
    <>
      <rect x="14" y="4" width="72" height="92" rx="7" fill={BLUE} />
      <rect x="22" y="12" width="56" height="56" rx="3" fill={WHITE} />
      <g transform="translate(22 12) scale(0.56)">{children}</g>
    </>
  );
}
function Slash({ count = 1, color = RED }: { count?: 1 | 2; color?: string }) {
  return (
    <g stroke={color} strokeWidth="8">
      <line x1="20" y1="80" x2="80" y2="20" />
      {count === 2 && <line x1="20" y1="20" x2="80" y2="80" />}
    </g>
  );
}

const SIGN_RENDER: Record<string, () => React.ReactNode> = {
  "1.1": () => <Warning>{pict.fence({ c: BLACK })}</Warning>,
  "1.2": () => <Warning>{pict.train({ c: BLACK })}</Warning>,
  "1.3.1": () => (
    <g><g transform="rotate(45 50 50)"><rect x="44" y="0" width="12" height="100" fill={RED} stroke={WHITE} strokeWidth="2" /><rect x="0" y="44" width="100" height="12" fill={RED} stroke={WHITE} strokeWidth="2" /></g></g>
  ),
  "1.3.2": () => (
    <g><g transform="rotate(45 50 40)"><rect x="44" y="-10" width="12" height="100" fill={RED} stroke={WHITE} strokeWidth="2" /><rect x="0" y="34" width="100" height="12" fill={RED} stroke={WHITE} strokeWidth="2" /></g><path d="M38 84 L50 70 L62 84" stroke={RED} strokeWidth="8" fill="none" /></g>
  ),
  "1.5": () => <Warning>{pict.tram({ c: BLACK })}</Warning>,
  "1.6": () => <Warning>{pict.cross({ c: BLACK })}</Warning>,
  "1.7": () => <Warning>{pict.roundabout({ c: BLACK })}</Warning>,
  "1.8": () => <Warning>{pict.light({ c: BLACK })}</Warning>,
  "1.11.1": () => <Warning>{pict.curveR({ c: BLACK })}</Warning>,
  "1.11.2": () => <Warning>{pict.curveL({ c: BLACK })}</Warning>,
  "1.13": () => <Warning>{pict.slopeDown({ c: BLACK })}</Warning>,
  "1.14": () => <Warning>{pict.slopeUp({ c: BLACK })}</Warning>,
  "1.15": () => <Warning>{pict.slippery({ c: BLACK })}</Warning>,
  "1.16": () => <Warning>{pict.bumps({ c: BLACK })}</Warning>,
  "1.18.1": () => <Warning>{pict.narrow({ c: BLACK })}</Warning>,
  "1.19": () => <Warning>{pict.twoWay({ c: BLACK })}</Warning>,
  "1.20": () => <Warning>{pict.ped({ c: BLACK })}</Warning>,
  "1.21": () => <Warning>{pict.children({ c: BLACK })}</Warning>,
  "1.22": () => <Warning>{pict.bike({ c: BLACK })}</Warning>,
  "1.23": () => <Warning>{pict.works({ c: BLACK })}</Warning>,
  "1.24": () => <Warning>{pict.cow({ c: BLACK })}</Warning>,
  "1.25.1": () => <Warning>{pict.deer({ c: BLACK })}</Warning>,
  "1.26": () => <Warning>{pict.rocks({ c: BLACK })}</Warning>,
  "1.30": () => <Warning>{pict.excl({ c: BLACK })}</Warning>,
  "1.31": () => <Warning>{pict.hump({ c: BLACK })}</Warning>,

  "2.1": () => (
    <g transform="rotate(45 50 50)"><rect x="18" y="18" width="64" height="64" fill={WHITE} stroke="#999" strokeWidth="1.5" /><rect x="27" y="27" width="46" height="46" fill={YELLOW} /></g>
  ),
  "2.2": () => (
    <g>
      <g transform="rotate(45 50 50)"><rect x="18" y="18" width="64" height="64" fill={WHITE} stroke="#999" strokeWidth="1.5" /><rect x="27" y="27" width="46" height="46" fill={YELLOW} /></g>
      <g stroke={BLACK} strokeWidth="3">{[-8, -3, 2, 7].map((o) => <line key={o} x1={26 + o} y1={74 + o} x2={74 + o} y2={26 + o} />)}</g>
    </g>
  ),
  "2.3.1": () => <Warning>{pict.crossMain({ c: BLACK })}</Warning>,
  "2.4": () => (
    <g><path d="M6 10 H94 Q98 10 96 14 L52 92 Q50 95 48 92 L4 14 Q2 10 6 10 Z" fill={RED} /><path d="M20 20 H80 L50 74 Z" fill={WHITE} /></g>
  ),
  "2.5": () => (
    <g>
      <path d="M31 4 H69 L96 31 V69 L69 96 H31 L4 69 V31 Z" fill={RED} />
      <path d="M33 9 H67 L91 33 V67 L67 91 H33 L9 67 V33 Z" fill="none" stroke={WHITE} strokeWidth="2.5" />
      <text x="50" y="50" dy="0.36em" textAnchor="middle" fontSize="27" fontWeight="800" fontFamily="Arial" fill={WHITE}>STOP</text>
    </g>
  ),
  "2.6": () => (
    <RoundProhib>
      <path d="M36 80 V40 H28 L40 22 L52 40 H44 V80 Z" fill={RED} />
      <path d="M64 22 V62 H72 L60 80 L48 62 H56 V22 Z" fill={BLACK} transform="translate(8 0)" />
    </RoundProhib>
  ),
  "2.7": () => (
    <Info>
      <path d="M38 80 V40 H30 L42 22 L54 40 H46 V80 Z" fill={WHITE} />
      <path d="M62 22 V62 H70 L58 80 L46 62 H54 V22 Z" fill={RED} transform="translate(10 0)" />
    </Info>
  ),

  "3.1": () => <g><circle cx="50" cy="50" r="46" fill={RED} /><rect x="18" y="41" width="64" height="18" fill={WHITE} /></g>,
  "3.2": () => <RoundProhib />,
  "3.3": () => <RoundProhib>{pict.car({ c: BLACK })}</RoundProhib>,
  "3.4": () => <RoundProhib>{pict.truck({ c: BLACK })}</RoundProhib>,
  "3.9": () => <RoundProhib>{pict.bike({ c: BLACK })}</RoundProhib>,
  "3.10": () => <RoundProhib>{pict.ped({ c: BLACK })}</RoundProhib>,
  "3.13": () => (
    <RoundProhib>
      <Num n="3.5" c={BLACK} size={30} />
      <path d="M50 4 L58 16 H42 Z M50 96 L42 84 H58 Z" fill={BLACK} />
    </RoundProhib>
  ),
  "3.18.1": () => <RoundProhib>{pict.curveR({ c: BLACK })}<Slash /></RoundProhib>,
  "3.18.2": () => <RoundProhib>{pict.curveL({ c: BLACK })}<Slash /></RoundProhib>,
  "3.19": () => <RoundProhib>{pict.uTurn({ c: BLACK })}<Slash /></RoundProhib>,
  "3.20": () => <RoundProhib>{pict.car2({ c: BLACK })}</RoundProhib>,
  "3.21": () => <EndOf>{pict.car2({ c: BLACK })}</EndOf>,
  "3.22": () => <RoundProhib><g transform="translate(-14 4) scale(0.8) translate(12 6)">{pict.truck({ c: RED })}</g><g transform="translate(16 4) scale(0.8) translate(12 6)">{pict.car({ c: BLACK })}</g></RoundProhib>,
  "3.24": () => <RoundProhib><Num n="60" c={BLACK} size={44} /></RoundProhib>,
  "3.25": () => <EndOf><Num n="60" c={BLACK} size={44} /></EndOf>,
  "3.26": () => <RoundProhib>{pict.horn({ c: BLACK })}<Slash /></RoundProhib>,
  "3.27": () => <g><circle cx="50" cy="50" r="46" fill={RED} /><circle cx="50" cy="50" r="36" fill={BLUE} /><g stroke={RED} strokeWidth="8"><line x1="25" y1="25" x2="75" y2="75" /><line x1="75" y1="25" x2="25" y2="75" /></g></g>,
  "3.28": () => <g><circle cx="50" cy="50" r="46" fill={RED} /><circle cx="50" cy="50" r="36" fill={BLUE} /><line x1="25" y1="25" x2="75" y2="75" stroke={RED} strokeWidth="8" /></g>,
  "3.31": () => <EndOf />,

  "4.1.1": () => <Mandatory>{pict.arrowUp({ c: WHITE })}</Mandatory>,
  "4.1.2": () => <Mandatory>{pict.curveR({ c: WHITE })}</Mandatory>,
  "4.1.3": () => <Mandatory>{pict.curveL({ c: WHITE })}</Mandatory>,
  "4.1.4": () => <Mandatory>{pict.arrowUpRight({ c: WHITE })}</Mandatory>,
  "4.2.1": () => <Mandatory><path d="M68 22 L36 60 V48 H26 L40 78 L54 66 H44 Z" fill={WHITE} transform="scale(-1 1) translate(-100 0)" /></Mandatory>,
  "4.2.2": () => <Mandatory><path d="M68 22 L36 60 V48 H26 L40 78 L54 66 H44 Z" fill={WHITE} transform="translate(4 0)" /></Mandatory>,
  "4.3": () => <Mandatory>{pict.roundabout({ c: WHITE })}</Mandatory>,
  "4.5": () => <Mandatory>{pict.bike({ c: WHITE })}</Mandatory>,
  "4.6": () => <Mandatory>{pict.ped({ c: WHITE })}</Mandatory>,
  "4.7": () => <Mandatory><Num n="30" c={WHITE} size={42} /></Mandatory>,

  "5.1": () => <Info bg="#1a8a3c">{pict.motorway({ c: WHITE })}</Info>,
  "5.5": () => <Info>{pict.arrowUp({ c: WHITE })}</Info>,
  "5.9": () => <Info>{pict.busLane({ c: WHITE })}</Info>,
  "5.12": () => <Info>{pict.bus({ c: WHITE })}</Info>,
  "5.15": () => <Info>{pict.pLetter({ c: WHITE })}</Info>,
  "5.16.1": () => <Info>{pict.pedCross({ c: WHITE })}</Info>,
  "5.22": () => (
    <g><rect x="4" y="26" width="92" height="48" rx="4" fill={WHITE} stroke={BLACK} strokeWidth="3" /><text x="50" y="50" dy="0.36em" textAnchor="middle" fontSize="17" fontWeight="700" fontFamily="Arial" fill={BLACK}>TOSHKENT</text></g>
  ),
  "5.23": () => (
    <g><rect x="4" y="26" width="92" height="48" rx="4" fill={WHITE} stroke={BLACK} strokeWidth="3" /><text x="50" y="50" dy="0.36em" textAnchor="middle" fontSize="17" fontWeight="700" fontFamily="Arial" fill={BLACK}>TOSHKENT</text><line x1="10" y1="70" x2="90" y2="30" stroke={RED} strokeWidth="6" /></g>
  ),
  "5.33": () => <Info>{pict.stopline({ c: WHITE })}</Info>,
  "5.38": () => <Info>{pict.house({ c: WHITE })}</Info>,
  "5.39": () => <Info>{pict.house({ c: WHITE })}<line x1="8" y1="92" x2="92" y2="8" stroke={RED} strokeWidth="7" /></Info>,

  "6.1": () => <Service>{pict.medical({ c: RED })}</Service>,
  "6.3.1": () => <Service>{pict.fuel({ c: BLACK })}</Service>,
  "6.11": () => <Service>{pict.rest({ c: BLACK })}</Service>,
};

function fallback(code: string) {
  const g = code.split(".")[0];
  const label = <Num n={code} c={g === "4" || g === "5" || g === "6" ? WHITE : BLACK} size={code.length > 4 ? 20 : 26} />;
  if (g === "1") return <Warning><g transform="translate(-17 -30) scale(1.5)">{label}</g></Warning>;
  if (g === "3") return <RoundProhib>{label}</RoundProhib>;
  if (g === "4") return <Mandatory>{label}</Mandatory>;
  return <Info>{label}</Info>;
}

export function hasSignArt(code: string) {
  return code in SIGN_RENDER;
}

export function SignIcon({ code, className, title }: { code: string; className?: string; title?: string }) {
  const render = SIGN_RENDER[code];
  return (
    <svg viewBox="0 0 100 100" className={cn("h-16 w-16 drop-shadow-sm", className)} role="img" aria-label={title ?? `Yo'l belgisi ${code}`}>
      {title && <title>{title}</title>}
      {render ? render() : fallback(code)}
    </svg>
  );
}

/** SVG ichida joylashtirish uchun (masalan, chorraha sxemasida) */
export function SignSvg({ code, x, y, size }: { code: string; x: number; y: number; size: number }) {
  const render = SIGN_RENDER[code];
  return (
    <svg x={x} y={y} width={size} height={size} viewBox="0 0 100 100" aria-hidden>
      {render ? render() : fallback(code)}
    </svg>
  );
}
