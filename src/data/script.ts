/**
 * Video ssenariysi — yagona manba (single source of truth).
 *
 * Har bir sahna uchun:
 *  - `segments`  : ekranda chiqadigan va ovozda o'qiladigan matn bo'laklari.
 *                  Ovoz (TTS) shu bo'laklar ketma-ket qo'shilganidan hosil bo'ladi,
 *                  so'zlar esa ovoz davomiyligiga proporsional ravishda chiqadi.
 *  - `voiceover` : public/ ichidagi ovoz fayli (topilmasa — davomiylik matndan taxmin qilinadi).
 *  - `image`     : public/images/<id>.(png|jpg|jpeg|webp) — AI rasm (ixtiyoriy).
 *  - `imagePrompt`: Gemini / Microsoft Designer uchun tayyor prompt.
 */

export type TransitionKind =
  | 'fade'
  | 'slide-left'
  | 'slide-up'
  | 'wipe'
  | 'flip'
  | 'clock'
  | 'iris'
  | 'push';

export type Segment = {
  text: string;
  /** Ajratib ko'rsatiladigan so'zlar (gradient + chiziq) */
  highlight?: string[];
};

export type SceneConfig = {
  id: string;
  title: string;
  segments: Segment[];
  /** TTS uchun ohang ko'rsatmasi (Gemini TTS style prompt) */
  ttsStyle: string;
  /** Sahnaning asosiy rangi (fon shu rangga yumshoq o'tadi) */
  accent: string;
  /** Animatsiya uchun minimal davomiylik (soniya) */
  minSeconds: number;
  /** Shu sahnadan keyingi o'tish turi */
  transitionOut: TransitionKind;
  imagePrompt: string;
};

export const IMAGE_STYLE =
  'cinematic food photography, warm rim light, shallow depth of field, rich saffron and amber tones, ' +
  'modern dark teal background, ultra detailed, 16:9, no text, no watermark';

export const SCENES: SceneConfig[] = [
  {
    id: '01-hook',
    title: 'Hook',
    segments: [
      {text: 'Ovqat sovidi,', highlight: ['sovidi,']},
      {text: 'surat hali tayyor emas!', highlight: ['surat']},
    ],
    ttsStyle: 'Energetic, playful and surprised, like the start of a funny social video',
    accent: '#FF8A3D',
    minSeconds: 3.6,
    transitionOut: 'push',
    imagePrompt:
      'A smartphone held above a steaming plate of Uzbek plov (osh) in a modern restaurant, camera flash, ' +
      IMAGE_STYLE,
  },
  {
    id: '02-intro',
    title: 'Fotosessiya',
    segments: [
      {text: 'Restoranga ovqat yeyishga keladi-yu,'},
      {
        text: 'avval palovga fotosessiya uyushtiradigan odamlarni bilasizmi?',
        highlight: ['fotosessiya'],
      },
    ],
    ttsStyle: 'Friendly storyteller, light ironic smile in the voice',
    accent: '#8B5CF6',
    minSeconds: 5,
    transitionOut: 'slide-left',
    imagePrompt:
      'Cozy modern Uzbek restaurant interior, friends at a table, one person photographing a big plate of plov with a phone, ' +
      IMAGE_STYLE,
  },
  {
    id: '03-hot-plov',
    title: 'Issiq palov',
    segments: [
      {text: 'Issiq palov keldi,', highlight: ['Issiq']},
      {text: 'bug‘i chiqib turibdi.', highlight: ['bug‘i']},
      {text: 'Hamma qoshiq olishga tayyor!', highlight: ['tayyor!']},
    ],
    ttsStyle: 'Warm, appetizing, excited',
    accent: '#F59E0B',
    minSeconds: 5,
    transitionOut: 'wipe',
    imagePrompt:
      'Hero shot of traditional Uzbek plov on a blue-white lagan plate, golden rice, carrots, tender lamb, garlic head on top, thick rising steam, ' +
      IMAGE_STYLE,
  },
  {
    id: '04-stop',
    title: 'To‘xtanglar!',
    segments: [
      {text: 'Birdan bittasi baqiradi:'},
      {text: '— To‘xtanglar!', highlight: ['To‘xtanglar!']},
      {text: 'Hali suratga olmadim!'},
    ],
    ttsStyle: 'Narration then a sudden loud comedic shout for the quote',
    accent: '#EF4444',
    minSeconds: 4.5,
    transitionOut: 'iris',
    imagePrompt:
      'Comic moment: a hand raised in a stop gesture over a plate of plov while friends freeze with spoons in the air, ' +
      IMAGE_STYLE,
  },
  {
    id: '05-photoshoot',
    title: 'Fotosessiya boshlandi',
    segments: [
      {text: 'Tepadan, yonidan,', highlight: ['Tepadan,', 'yonidan,']},
      {text: 'go‘shtini yaqinlashtirib…', highlight: ['go‘shtini']},
      {text: 'Keyin selfi, musiqa, joylashuv!', highlight: ['selfi,', 'musiqa,', 'joylashuv!']},
    ],
    ttsStyle: 'Fast, rhythmic, comedic list',
    accent: '#22D3EE',
    minSeconds: 6.5,
    transitionOut: 'slide-up',
    imagePrompt:
      'Top-down flat lay of Uzbek plov photographed with a smartphone, camera grid overlay feel, ' + IMAGE_STYLE,
  },
  {
    id: '06-waiting',
    title: 'Palov soviyapti',
    segments: [
      {text: 'Do‘stlar ochlikdan kutib o‘tiribdi,', highlight: ['ochlikdan']},
      {text: 'palov esa sovib qoldi.', highlight: ['sovib']},
    ],
    ttsStyle: 'Slower, dramatic, a little sad but funny',
    accent: '#38BDF8',
    minSeconds: 5,
    transitionOut: 'flip',
    imagePrompt:
      'Hungry bored friends waiting at a restaurant table, a plate of plov getting cold, cool blue light, ' +
      IMAGE_STYLE,
  },
  {
    id: '07-passport',
    title: 'Palov pasporti',
    segments: [
      {text: 'Shunda bittasi so‘raydi:'},
      {
        text: '— Do‘stim, ovqat yeymizmi yoki palovga pasport tayyorlaymizmi?',
        highlight: ['pasport'],
      },
    ],
    ttsStyle: 'Sarcastic friendly question, comedic timing',
    accent: '#10B981',
    minSeconds: 6,
    transitionOut: 'clock',
    imagePrompt:
      'Funny concept: an official-looking passport document with a photo of a plate of Uzbek plov, ' + IMAGE_STYLE,
  },
  {
    id: '08-posted',
    title: 'Joylandi',
    segments: [
      {text: 'Nihoyat, surat internetga joylandi.', highlight: ['joylandi.']},
      {text: 'Lekin palovning issiqligi allaqachon yo‘qoldi!', highlight: ['yo‘qoldi!']},
    ],
    ttsStyle: 'Triumphant first, then disappointed',
    accent: '#EC4899',
    minSeconds: 6,
    transitionOut: 'fade',
    imagePrompt:
      'A social media post on a phone showing a beautiful plov photo with many likes, the real plate next to it is cold, ' +
      IMAGE_STYLE,
  },
  {
    id: '09-moral',
    title: 'Eng yaxshi filtr',
    segments: [
      {text: 'Axir palovning eng yaxshi filtri —', highlight: ['filtri']},
      {text: 'uning bug‘i,', highlight: ['bug‘i,']},
      {text: 'eng zo‘r vaqti esa issiqligida!', highlight: ['issiqligida!']},
    ],
    ttsStyle: 'Warm, wise, confident conclusion',
    accent: '#FB923C',
    minSeconds: 5.5,
    transitionOut: 'push',
    imagePrompt:
      'Close-up of fresh hot Uzbek plov with dramatic backlit steam, golden hour glow, ' + IMAGE_STYLE,
  },
  {
    id: '10-question',
    title: 'Savol',
    segments: [
      {text: 'Rostini ayting,'},
      {text: 'siz avval ovqatlanasizmi', highlight: ['ovqatlanasizmi']},
      {text: 'yoki suratga olasizmi?', highlight: ['suratga']},
    ],
    ttsStyle: 'Engaging direct question to the viewer, smiling',
    accent: '#A78BFA',
    minSeconds: 6.5,
    transitionOut: 'fade',
    imagePrompt:
      'Split composition: on the left a person happily eating plov, on the right a person photographing plov, ' +
      IMAGE_STYLE,
  },
];

export const narrationOf = (scene: SceneConfig) => scene.segments.map((s) => s.text).join(' ');
