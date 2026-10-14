import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {SCENES} from '../data/script';
import {useScene, useSegmentWindows} from '../lib/scene-context';
import {SceneTag} from '../components/visuals/ui';

export const useSceneBasics = () => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const {scene, timing} = useScene();
  const windows = useSegmentWindows();
  const index = SCENES.findIndex((s) => s.id === scene.id) + 1;
  return {frame, fps, width, height, scene, timing, windows, index};
};

/** Har bir sahna uchun umumiy ramka: xavfsiz chegaralar + sahna yorlig'i */
export const SceneFrame: React.FC<{children: React.ReactNode; tag?: boolean; style?: React.CSSProperties}> = ({
  children,
  tag = true,
  style,
}) => {
  const {scene, index} = useSceneBasics();
  return (
    <AbsoluteFill style={{padding: '96px 130px', ...style}}>
      {tag && (
        <div style={{position: 'absolute', top: 64, left: 130}}>
          <SceneTag index={index} total={SCENES.length} label={scene.title} color={scene.accent} />
        </div>
      )}
      {children}
    </AbsoluteFill>
  );
};
