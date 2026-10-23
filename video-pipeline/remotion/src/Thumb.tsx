import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import '@fontsource/oswald/700.css';
import '@fontsource/montserrat/800.css';

export const Thumb: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    <Img src={staticFile('imgs/00.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.15) translateX(-12%)', filter: 'contrast(1.2) saturate(0.8) brightness(0.9)'}} />
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(0,0,0,0) 35%, rgba(0,0,0,0.85) 70%)'}} />
    <AbsoluteFill style={{alignItems: 'flex-end', justifyContent: 'center', paddingRight: 90}}>
      <div style={{fontFamily: 'Oswald', fontWeight: 700, fontSize: 300, lineHeight: 0.9, color: '#ffd166', textShadow: '0 10px 40px #000'}}>29 YIL</div>
      <div style={{fontFamily: 'Oswald', fontWeight: 700, fontSize: 110, lineHeight: 1.0, color: '#fff', textAlign: 'right', textShadow: '0 8px 30px #000'}}>O‘RMONDA<br />URUSHDA</div>
      <div style={{marginTop: 26, fontFamily: 'Montserrat', fontWeight: 800, fontSize: 46, color: '#fff', background: '#c8352b', padding: '10px 26px'}}>URUSH ALLAQACHON TUGAGAN EDI</div>
    </AbsoluteFill>
  </AbsoluteFill>
);
