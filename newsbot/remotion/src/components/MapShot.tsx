import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {geoMercator, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import world from 'world-atlas/countries-50m.json';
import {MapSpec} from '../types';
import {theme} from '../theme';

// Natural Earth (public domain) country shapes.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries = (feature(world as any, (world as any).objects.countries) as any).features as any[];

const W = 1080;
const H = 1920;

export const MapShot: React.FC<{spec: MapSpec; durFrames: number}> = ({spec, durFrames}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const z = interpolate(frame, [0, Math.min(durFrames, fps * 1.8)], [spec.zoomFrom, spec.zoomTo], {
		extrapolateRight: 'clamp',
		easing: Easing.inOut(Easing.cubic),
	});
	const projection = geoMercator().center(spec.center).scale(z).translate([W / 2, H * 0.44]);
	const path = geoPath(projection);
	const hl = new Set(spec.highlight ?? []);
	const glow = 0.55 + 0.45 * Math.abs(Math.sin(frame / 10));
	const labelIn = spring({frame: frame - fps * 0.9, fps, config: {damping: 200}});
	const focus = countries.find((c) => hl.has(String(c.id)));
	const focusBox = focus ? path.bounds(focus) : null; // [[x0,y0],[x1,y1]]
	return (
		<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 42%, #0b1a30 0%, #04070d 75%)'}}>
			<svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
				<defs>
					<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
						<feGaussianBlur stdDeviation="10" result="b" />
						<feMerge>
							<feMergeNode in="b" />
							<feMergeNode in="SourceGraphic" />
						</feMerge>
					</filter>
				</defs>
				{/* graticule-like grid */}
				{Array.from({length: 24}).map((_, i) => (
					<line key={`g${i}`} x1={0} x2={W} y1={i * 80} y2={i * 80} stroke="rgba(255,255,255,0.04)" strokeWidth={2} />
				))}
				{countries.map((c, i) => {
					const isHl = hl.has(String(c.id));
					return (
						<path
							key={i}
							d={path(c) ?? ''}
							fill={isHl ? theme.red : '#25395a'}
							fillOpacity={isHl ? 0.55 + 0.35 * glow : 1}
							stroke={isHl ? '#ff6b6b' : '#4a6488'}
							strokeWidth={isHl ? 3 : 1.2}
							filter={isHl ? 'url(#glow)' : undefined}
						/>
					);
				})}
				{(spec.pins ?? []).map((p, i) => {
					const xy = projection([p.lon, p.lat]);
					if (!xy) return null;
					const s = spring({frame: frame - fps * (1.1 + i * 0.35), fps, config: {damping: 12}});
					const pulse = 1 + 0.6 * ((frame / 18 + i * 0.3) % 1);
					const col = p.main ? theme.yellow : '#fff';
					return (
						<g key={`p${i}`} transform={`translate(${xy[0]},${xy[1]}) scale(${s})`}>
							<circle r={18 * pulse} fill="none" stroke={col} strokeOpacity={1.6 - pulse} strokeWidth={4} />
							<circle r={13} fill={col} stroke="#000" strokeWidth={3} />
							{/* label goes left of the pin when it would run off the right edge */}
							{(() => {
								const w = p.name.length * 24 + 34;
								const left = xy[0] + 26 + w > W - 40;
								const x0 = left ? -26 - w : 26;
								return (
									<>
										<rect x={x0} y={-30} rx={10} width={w} height={60} fill="rgba(7,11,20,.85)" stroke={col} strokeWidth={2} />
										<text x={x0 + 17} y={12} fill={col} fontFamily="Inter" fontWeight={800} fontSize={36}>
											{p.name}
										</text>
									</>
								);
							})()}
							<text x={-10000} y={0} fill={col} fontFamily="Inter" fontWeight={800} fontSize={1}>
								{p.name}
							</text>
						</g>
					);
				})}
			</svg>
			{spec.label && focusBox ? (
				<div
					style={{
						position: 'absolute',
						left: 0,
						right: 0,
						top: Math.max(260, focusBox[0][1] - 110),
						textAlign: 'center',
						opacity: labelIn,
						transform: `translateY(${(1 - labelIn) * 30}px)`,
						fontFamily: theme.font,
						fontWeight: 900,
						fontSize: 64,
						letterSpacing: 6,
						color: '#fff',
						textShadow: '0 4px 30px rgba(0,0,0,.9)',
					}}
				>
					{spec.label}
				</div>
			) : null}
		</AbsoluteFill>
	);
};
