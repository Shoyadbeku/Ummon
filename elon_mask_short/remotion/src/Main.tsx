import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Captions} from './Captions';
import {
  ANTON, CompanyCard, Counter, CTA, CYAN, f, FPS, GOLD, Grain, GREEN, Headline, LightLeak, MONT, NightClock, OVER, Pill,
  ProgressBar, RED, RetroBrowser, Scanlines, Shake, Shot, SpeedLines, Stamp, Vignette, YearRoll, YELLOW, Zzz,
} from './fx';

const GOLD_GRAD = 'linear-gradient(180deg,#FFF6C8 0%,#FFD23F 45%,#E89B0C 100%)';
const ICE_GRAD = 'linear-gradient(180deg,#FFFFFF 0%,#BFF4FF 50%,#4FE3FF 100%)';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ---------------------------------------------------------------- custom scenes
const Brothers: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame, fps, config: {damping: 15, stiffness: 170}});
  const b = spring({frame: frame - 7, fps, config: {damping: 15, stiffness: 170}});
  const panel = (src: string, s: number, dir: number, pos: string): React.CSSProperties => ({
    position: 'absolute', top: 0, bottom: 0, width: '50%', overflow: 'hidden',
    transform: `translateY(${(1 - s) * 1920 * dir}px)`, [dir < 0 ? 'left' : 'right']: 0,
  });
  return (
    <AbsoluteFill style={{backgroundColor: '#05060a'}}>
      <div style={panel('', a, -1, '')}>
        <Img src={staticFile('img/musk_young.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 20%', transform: `scale(${1.15 - frame * 0.002})`, filter: 'contrast(1.1) saturate(1.05)'}} />
      </div>
      <div style={panel('', b, 1, '')}>
        <Img src={staticFile('img/kimbal.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '45% 25%', transform: `scale(${1.1 + frame * 0.002})`, filter: 'contrast(1.1) saturate(1.05)'}} />
      </div>
      <div style={{position: 'absolute', left: 537, top: 0, bottom: 0, width: 6, background: YELLOW, boxShadow: `0 0 30px ${YELLOW}`, transform: `scaleY(${b})`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,0.7) 100%)'}} />
    </AbsoluteFill>
  );
};

const ShowerGym: React.FC<{gymAt: number}> = ({gymAt}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const top = spring({frame, fps, config: {damping: 15}});
  const bot = spring({frame: frame - gymAt, fps, config: {damping: 15}});
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  const vid: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover'};
  return (
    <AbsoluteFill style={{backgroundColor: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateX(${(1 - top) * -1080}px)`, filter: frame >= gymAt ? 'brightness(0.55) saturate(0.6)' : 'none'}}>
        <OffthreadVideo src={staticFile('v/shower.mp4')} muted style={{...vid, filter: 'contrast(1.15) saturate(1.1) hue-rotate(-10deg)'}} />
      </div>
      <div style={{...half, top: 965, transform: `translateX(${(1 - bot) * 1080}px)`}}>
        <OffthreadVideo src={staticFile('v/gym.mp4')} muted style={{...vid, objectPosition: '55% 50%', filter: 'contrast(1.15) saturate(1.1)'}} />
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: YELLOW, boxShadow: `0 0 30px ${YELLOW}`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0) 25%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};

const FinalSplit: React.FC<{mehnatAt: number; daholikAt: number}> = ({mehnatAt, daholikAt}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame, fps, config: {damping: 15}});
  const b = spring({frame: frame - 5, fps, config: {damping: 15}});
  const mActive = frame >= mehnatAt && frame < daholikAt;
  const dActive = frame >= daholikAt;
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  const label = (txt: string, color: string, on: boolean, s: number): React.CSSProperties => ({
    position: 'absolute', left: 0, right: 0, textAlign: 'center', fontFamily: ANTON, fontSize: on ? 190 : 150, color: on ? color : 'white',
    letterSpacing: 6, textShadow: `0 8px 0 rgba(0,0,0,0.6)${on ? `, 0 0 50px ${color}` : ''}`, transform: `scale(${s})`,
  });
  const mS = spring({frame: frame - mehnatAt, fps, config: {damping: 9, stiffness: 250}});
  const dS = spring({frame: frame - daholikAt, fps, config: {damping: 9, stiffness: 250}});
  return (
    <AbsoluteFill style={{backgroundColor: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateY(${(1 - a) * -960}px)`, filter: dActive ? 'brightness(0.5) grayscale(0.6)' : 'none'}}>
        <OffthreadVideo src={staticFile('v/work_hard.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 60%', filter: 'contrast(1.15) saturate(1.1)'}} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 45%)'}} />
        {frame >= mehnatAt - 2 && <div style={{...label('MEHNAT?', YELLOW, mActive, mS), top: 230}}>MEHNAT?</div>}
      </div>
      <div style={{...half, top: 965, transform: `translateY(${(1 - b) * 960}px)`, filter: mActive ? 'brightness(0.5) grayscale(0.6)' : 'none'}}>
        <OffthreadVideo src={staticFile('v/brain_draw.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'contrast(1.2) saturate(1.1) brightness(0.95)'}} />
        <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 55%)'}} />
        {frame >= daholikAt - 2 && <div style={{...label('DAHOLIK?', GREEN, dActive, dS), top: 300}}>DAHOLIK?</div>}
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: 'white', boxShadow: '0 0 30px white'}} />
    </AbsoluteFill>
  );
};

const PortraitHero: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 13, stiffness: 150}});
  const ring = interpolate(frame, [0, 30], [0, 360], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', top: 470}}>
      <div style={{width: 620, height: 620, borderRadius: '50%', padding: 12, transform: `scale(${s})`,
        background: `conic-gradient(${GOLD} 0deg, ${CYAN} ${ring / 2}deg, ${GOLD} ${ring}deg, rgba(255,255,255,0.1) ${ring}deg)`,
        boxShadow: `0 0 90px rgba(255,210,63,0.55)`}}>
        <Img src={staticFile('img/musk_2015.jpg')} style={{width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover', objectPosition: '50% 25%', transform: `scale(${1.05 + frame * 0.003})`}} />
      </div>
    </AbsoluteFill>
  );
};

const RewindTag: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{position: 'absolute', left: 70, top: 230, fontFamily: 'monospace', fontWeight: 700, fontSize: 64, color: 'white', textShadow: '0 0 12px rgba(255,255,255,0.8)', opacity: frame % 20 < 14 ? 1 : 0.2}}>
      ◀◀ REWIND
    </div>
  );
};

const Sfx: React.FC<{src: string; at: number; vol?: number; dur?: number}> = ({src, at, vol = 0.5, dur = 3}) => (
  <Sequence from={Math.max(0, f(at))} durationInFrames={f(dur)} layout="none">
    <Audio src={staticFile(`audio/${src}.mp3`)} volume={vol} />
  </Sequence>
);

// ---------------------------------------------------------------- main
export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const captionY = t >= 35.98 ? 850 : 1300;

  return (
    <AbsoluteFill style={{backgroundColor: '#05060a'}}>
      <Shake at={0} dur={0.45} amp={22}>
        <Shake at={3.02} dur={0.35} amp={16}>
          <Shake at={23.98} dur={0.45} amp={20}>
            <Shake at={32.72} dur={0.6} amp={26}>
              {/* 1. HOOK ------------------------------------------------ */}
              <Shot src="v/hook_liftoff.mp4" from={0} to={1.44} enter="flash" kb={[1.45, 1.1]} grade="cine" />
              <Shot src="img/musk_dark.jpg" img from={1.44} to={3.84} enter="whip-up" kb={[1.28, 1.08]} pos="50% 18%" grade="contrast(1.15) saturate(1.05)" tint="linear-gradient(180deg, rgba(255,190,80,0.5), rgba(20,40,80,0.6))" />

              {/* 2. Night work -------------------------------------------- */}
              <Shot src="v/night_office.mp4" from={3.84} to={5.68} enter="whip-left" kb={[1.1, 1.22]} pos="60% 50%" grade="night" tint="rgba(30,80,200,0.6)" />
              <Shot src="v/laptop_night.mp4" from={5.68} to={7.22} enter="zoom" kb={[1.15, 1.3]} grade="night" tint="rgba(30,80,200,0.6)" />

              {/* 3. 1990s / brothers / Zip2 -------------------------------- */}
              <Shot src="v/matrix.mp4" from={7.22} to={8.98} enter="flash" kb={[1.3, 1.5]} grade="contrast(1.3) saturate(1.3) brightness(0.45)">
                <Scanlines opacity={0.35} />
              </Shot>
              <Sequence from={f(8.98)} durationInFrames={f(9.94) - f(8.98) + OVER} layout="none"><Brothers /></Sequence>
              <Shot src="v/worldmap.mp4" from={9.94} to={12.8} enter="mask" kb={[1.2, 1.45]} grade="contrast(1.2) brightness(0.55) saturate(1.2)" tint="rgba(0,120,255,0.5)" />

              {/* 4. Saving money / sleeping in office ---------------------- */}
              <Shot src="v/coins.mp4" from={12.8} to={14.22} enter="whip-up" kb={[1.1, 1.25]} pos="40% 50%" grade="warm" />
              <Shot src="v/sleeping_desk.mp4" from={14.22} to={15.68} enter="whip-left" kb={[1.12, 1.28]} pos="30% 50%" grade="night" />

              {/* 5. Shower + gym split ------------------------------------- */}
              <Sequence from={f(15.68)} durationInFrames={f(17.98) - f(15.68) + OVER} layout="none"><ShowerGym gymAt={f(16.84) - f(15.68)} /></Sequence>

              {/* 6. 1999 sale -------------------------------------------- */}
              <Shot src="v/banknotes.mp4" from={17.98} to={20.72} enter="flash" kb={[1.1, 1.3]} grade="money" />
              <Shot src="v/money_machine.mp4" from={20.72} to={22.64} enter="zoom" kb={[1.2, 1.35]} grade="money" />

              {/* 7. He didn't stop ---------------------------------------- */}
              <Shot src="v/car_pov.mp4" from={22.64} to={24.56} enter="whip-up" kb={[1.15, 1.45]} rate={2} grade="cine">
                <SpeedLines opacity={0.45} />
              </Shot>

              {/* 8. PayPal / Tesla / SpaceX timeline ----------------------- */}
              <Shot src="v/earth.mp4" from={24.56} to={27.78} enter="zoom" kb={[1.2, 1.35]} grade="dark" />
              <Shot src="img/tesla_factory.jpg" img from={27.78} to={28.9} enter="whip-left" kb={[1.15, 1.3]} drift={[-60, 0]} pos="70% 50%" grade="cine" />
              <Shot src="img/starship.jpg" img from={28.9} to={30.5} enter="flash" kb={[1.05, 1.25]} drift={[0, 30]} pos="50% 60%" grade="cine" />

              {/* 9. Flashback ---------------------------------------------- */}
              <Shot src="v/asleep_flashback.mp4" from={30.5} to={32.72} enter="whip-right" kb={[1.2, 1.35]} pos="55% 50%" grade="bw" rate={0.8}>
                <Scanlines opacity={0.3} />
                <RewindTag />
              </Shot>

              {/* 10. THE DROP: rockets ------------------------------------- */}
              <Shot src="v/liftoff_close.mp4" from={32.72} to={33.88} enter="flash" startFrom={0.5} kb={[1.35, 1.15]} pos="45% 50%" grade="cine" />
              <Shot src="v/booster_landing.mp4" from={33.88} to={34.4} enter="whip-up" startFrom={1.5} kb={[1.2, 1.3]} grade="cine" />
              <Shot src="v/orbit.mp4" from={34.4} to={34.9} enter="zoom" kb={[1.3, 1.4]} pos="40% 50%" grade="cine" />
              <Shot src="v/orbit.mp4" from={34.9} to={35.98} enter="cut" startFrom={0.5} kb={[1.4, 1.5]} pos="40% 50%" grade="dark">
                <PortraitHero />
              </Shot>

              {/* 11. Question ending -------------------------------------- */}
              <Sequence from={f(35.98)} durationInFrames={f(39.37) - f(35.98) + 2} layout="none">
                <FinalSplit mehnatAt={f(36.98) - f(35.98)} daholikAt={f(38.42) - f(35.98)} />
              </Sequence>
            </Shake>
          </Shake>
        </Shake>
      </Shake>

      {/* ---------------- motion graphics layer ---------------- */}
      <Headline text="DUNYONING" at={0.48} until={1.44} y={330} size={140} />
      <Headline text="ENG BOY" at={1.08} until={3.0} y={880} size={250} gradient={GOLD_GRAD} glow="rgba(255,200,60,0.7)" />
      <Headline text={'ILON\nMASK'} at={3.02} until={3.84} y={760} size={240} gradient={GOLD_GRAD} glow="rgba(255,200,60,0.8)" stagger={1.5} letterSpacing={10} />

      <NightClock at={3.95} until={7.22} y={300} />
      <Headline text="TUNAB ISHLAGAN" at={5.68} until={7.22} y={850} size={130} color="white" />
      <Headline text="?" at={6.6} until={7.22} y={960} size={200} color={YELLOW} />

      <YearRoll at={7.22} until={8.98} y={520} />
      <Pill text="Ilon" at={9.0} until={9.94} x={270} y={1040} bg={YELLOW} />
      <Pill text="Ukasi" at={9.22} until={9.94} x={810} y={1040} bg={GREEN} from="right" />
      <RetroBrowser at={9.94} until={12.8} y={330} stampAt={12.08} />

      <Headline text="PULNI TEJASH" at={13.3} until={14.22} y={360} size={150} gradient={GOLD_GRAD} />
      <Headline text={'OFISDA\nUXLAGAN'} at={14.76} until={15.68} y={300} size={160} color="white" />
      <Zzz at={14.5} until={15.68} x={330} y={900} />

      <Pill text="Dush" at={15.75} until={17.98} x={540} y={420} bg={CYAN} />
      <Pill text="Sport zali" at={16.84} until={17.98} x={540} y={1080} bg={YELLOW} from="right" />

      <Headline text="1999" at={17.98} until={20.72} y={330} size={300} gradient={GOLD_GRAD} glow="rgba(255,200,60,0.7)" letterSpacing={12} />
      <Pill text="Zip2 sotuvi" at={19.84} until={20.72} x={540} y={700} bg="white" />
      <Counter at={20.72} until={22.64} to={307000000} y={430} dur={1.1} />
      <Pill text="≈ 307 million dollar" at={21.36} until={22.64} x={540} y={640} bg={GREEN} />
      <Stamp text="SOTILDI" at={22.2} until={22.64} y={820} size={140} />

      <Headline text="AMMO..." at={22.7} until={23.98} y={420} size={170} color="white" />
      <Headline text={"TO'XTAMADI"} at={23.98} until={24.56} y={430} size={175} color={RED} stagger={0.8} />

      <CompanyCard idx={0} at={25.44} until={27.78} activeUntil={26.18} y={240} title="PAYPAL" color="#2F8BFF" src="img/paypal_hq.jpg" />
      <CompanyCard idx={1} at={26.18} until={27.78} activeUntil={26.9} y={610} title="TESLA" color={RED} src="img/tesla_factory.jpg" />
      <CompanyCard idx={2} at={26.9} until={27.78} activeUntil={27.78} y={980} title="SPACEX" color="white" src="v/spacex_close.mp4" video />
      <Headline text="KEYINCHALIK" at={24.6} until={25.44} y={700} size={150} color="white" />

      <Headline text={'ULKAN\nLOYIHALAR'} at={28.9} until={30.5} y={300} size={170} gradient={GOLD_GRAD} glow="rgba(255,200,60,0.6)" />

      <Headline text={'OFISDA\nUXLAGAN YIGIT'} at={31.42} until={32.72} y={760} size={130} color="white" />

      <Headline text="KOSMOSGA" at={33.36} until={34.4} y={330} size={210} gradient={ICE_GRAD} glow="rgba(79,227,255,0.8)" />
      <Headline text="RAKETALAR" at={33.88} until={34.9} y={560} size={190} color="white" />
      <Headline text="TADBIRKOR" at={34.9} until={35.98} y={260} size={200} gradient={GOLD_GRAD} glow="rgba(255,200,60,0.8)" />

      <CTA at={38.5} until={39.4} y={1110} text="Fikringizni yozing" />

      {/* ---------------- finishing layers ---------------- */}
      <LightLeak at={1.44} />
      <LightLeak at={7.22} hue="cool" />
      <LightLeak at={17.98} />
      <LightLeak at={24.56} hue="cool" />
      <LightLeak at={28.9} />
      <LightLeak at={32.72} dur={0.9} />
      <LightLeak at={35.98} hue="cool" />
      <Vignette />
      <Grain opacity={0.1} />
      <Captions y={captionY} />
      <ProgressBar />

      {/* ---------------- audio ---------------- */}
      <Audio src={staticFile('audio/voice_clean.wav')} volume={1} />
      <Audio
        src={staticFile('audio/music.mp3')}
        volume={(fr) => {
          const s = fr / FPS;
          const base = s < 32.6 ? 0.2 : 0.3; // lift at the drop
          const fadeIn = interpolate(s, [0, 0.4], [0.5, 1], clamp);
          const fadeOut = interpolate(s, [38.6, 39.37], [1, 0.25], clamp);
          return base * fadeIn * fadeOut;
        }}
      />
      <Sfx src="sfx_788" at={0} vol={0.55} dur={2.5} />
      <Sfx src="sfx_1715" at={0} vol={0.3} dur={1.5} />
      <Sfx src="sfx_1492" at={1.38} vol={0.45} dur={1.4} />
      <Sfx src="sfx_2908" at={3.0} vol={0.5} dur={2} />
      <Sfx src="sfx_1490" at={3.8} vol={0.35} dur={1.6} />
      <Sfx src="sfx_1059" at={4.0} vol={0.18} dur={3.1} />
      <Sfx src="sfx_1143" at={7.18} vol={0.4} dur={2.5} />
      <Sfx src="sfx_166" at={8.95} vol={0.4} dur={0.8} />
      <Sfx src="sfx_3120" at={9.9} vol={0.35} dur={1.6} />
      <Sfx src="sfx_772" at={12.06} vol={0.5} dur={1.2} />
      <Sfx src="sfx_1492" at={12.75} vol={0.3} dur={1.4} />
      <Sfx src="sfx_166" at={14.18} vol={0.3} dur={0.8} />
      <Sfx src="sfx_1490" at={15.64} vol={0.3} dur={1.6} />
      <Sfx src="sfx_166" at={16.8} vol={0.3} dur={0.8} />
      <Sfx src="sfx_2908" at={17.96} vol={0.4} dur={2.5} />
      <Sfx src="sfx_1053" at={20.72} vol={0.25} dur={1.15} />
      <Sfx src="sfx_772" at={22.18} vol={0.55} dur={1.2} />
      <Sfx src="sfx_1714" at={22.6} vol={0.35} dur={2} />
      <Sfx src="sfx_788" at={23.96} vol={0.3} dur={1.5} />
      <Sfx src="sfx_1492" at={24.52} vol={0.3} dur={1.4} />
      <Sfx src="sfx_3005" at={25.44} vol={0.5} dur={0.3} />
      <Sfx src="sfx_3005" at={26.18} vol={0.5} dur={0.3} />
      <Sfx src="sfx_3005" at={26.9} vol={0.5} dur={0.3} />
      <Sfx src="sfx_166" at={27.74} vol={0.3} dur={0.8} />
      <Sfx src="sfx_1143" at={28.86} vol={0.4} dur={2.5} />
      <Sfx src="sfx_1490" at={30.46} vol={0.3} dur={1.6} />
      <Sfx src="sfx_498" at={31.2} vol={0.35} dur={1.5} />
      <Sfx src="sfx_788" at={32.7} vol={0.6} dur={3} />
      <Sfx src="sfx_1715" at={32.72} vol={0.35} dur={2.2} />
      <Sfx src="sfx_1492" at={34.86} vol={0.3} dur={1.4} />
      <Sfx src="sfx_1143" at={35.94} vol={0.35} dur={2.5} />
      <Sfx src="sfx_772" at={36.96} vol={0.35} dur={1.2} />
      <Sfx src="sfx_772" at={38.4} vol={0.45} dur={0.97} />
    </AbsoluteFill>
  );
};
