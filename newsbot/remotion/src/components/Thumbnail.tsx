import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {theme} from '../theme';
import {Globe, UzFlag} from './Overlays';

// Designed cover / thumbnail (1080x1920). Key text sits in the centre so it survives
// the 4:5 grid crop on the Instagram profile and the 1:1 crop in some feeds.
export const Thumbnail: React.FC<{
	brand: string;
	kicker: string;
	region: 'uz' | 'world';
	text: string;
	headline: string;
	media?: string | null;
}> = ({brand, kicker, region, text, headline, media}) => {
	const lines = text.split(/\s*[|\n]\s*/);
	return (
		<AbsoluteFill style={{backgroundColor: theme.ink}}>
			{media ? (
				<Img src={staticFile(media)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'saturate(1.15) contrast(1.05)'}} />
			) : null}
			<AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,.15) 30%, rgba(0,0,0,.55) 55%, rgba(0,0,0,.92) 100%)'}} />
			<div style={{position: 'absolute', top: 60, left: 60, right: 60, display: 'flex', alignItems: 'center', gap: 18}}>
				<div style={{fontFamily: theme.font, fontWeight: 900, fontSize: 46, color: '#fff', padding: '8px 20px', background: theme.ink, borderRadius: 12}}>{brand}</div>
				<div style={{fontFamily: theme.font, fontWeight: 800, fontSize: 36, color: '#fff', padding: '10px 20px', background: theme.red, borderRadius: 12, textTransform: 'uppercase'}}>{kicker}</div>
				<div style={{marginLeft: 'auto'}}>{region === 'uz' ? <UzFlag w={84} /> : <Globe size={64} />}</div>
			</div>
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 60px'}}>
				<div style={{background: theme.yellow, color: theme.ink, fontFamily: theme.font, fontWeight: 900, fontSize: 40, padding: '10px 26px', borderRadius: 10, marginBottom: 26, letterSpacing: 1}}>
					MUHIM YANGILIK
				</div>
				{lines.map((l, i) => (
					<div
						key={i}
						style={{
							fontFamily: theme.font,
							fontWeight: 900,
							fontSize: lines.length > 2 ? 104 : 132,
							lineHeight: 1.0,
							color: i % 2 === 1 ? theme.yellow : '#fff',
							textAlign: 'center',
							textTransform: 'uppercase',
							letterSpacing: -2,
							textShadow: '0 8px 40px rgba(0,0,0,.85), 0 0 4px rgba(0,0,0,.9)',
						}}
					>
						{l}
					</div>
				))}
			</AbsoluteFill>
			<div style={{position: 'absolute', bottom: 380, left: 60, right: 60, borderLeft: `12px solid ${theme.red}`, paddingLeft: 24}}>
				<div style={{fontFamily: theme.font, fontWeight: 800, fontSize: 50, lineHeight: 1.12, color: '#fff', textShadow: '0 4px 20px rgba(0,0,0,.9)'}}>{headline}</div>
			</div>
		</AbsoluteFill>
	);
};
