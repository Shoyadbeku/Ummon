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
  '2D cartoon cutout characters with thick white sticker outline, warm cinematic Uzbek interior ' +
  '(carved wooden columns, suzani textiles, ikat cushions, blue-white lagan plates, tea pots), ' +
  'soft rim light, rich details, warm amber and saffron palette with teal accents, ' +
  'paper-cutout layered depth, 16:9 widescreen, no text, no letters, no watermark';

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
      'A young Uzbek man in a modern restaurant holds his smartphone high above a big steaming plate of plov, phone flash bursting, his friends laughing behind him, ' + IMAGE_STYLE,
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
      'Four Uzbek friends sitting at a low wooden table (tapchan) in a cozy chaikhana; one of them is arranging a plate of plov like a photo studio, with a small ring light, the others watching amused, ' + IMAGE_STYLE,
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
      'A waiter places a huge lagan of hot Uzbek plov with golden rice, carrots, lamb and a garlic head on the table, thick white steam rising, friends leaning in holding spoons ready to eat, ' + IMAGE_STYLE,
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
      'Funny freeze-frame: one friend jumps up shouting with a raised hand in a stop gesture, the other friends freeze with spoons in mid-air above the steaming plov, surprised faces, ' + IMAGE_STYLE,
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
      'The photographer friend on a chair shooting the plov from above, then from the side, a close-up of the meat on the phone screen, selfie pose, music notes and a location pin floating as stickers, ' + IMAGE_STYLE,
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
      'Hungry bored friends slumped at the table, one resting his chin on his hand, one yawning, a wall clock showing time passing, the plov with no more steam, cooler bluish light creeping in, ' + IMAGE_STYLE,
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
      'A friend with a skeptical raised eyebrow asks a question, beside him a giant comic passport document with a photo of the plov plate and an official stamp, ' + IMAGE_STYLE,
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
      'The photographer happily shows his phone with a social post full of hearts and likes, while his friends point sadly at the cold plov on the table, frost sticker on the plate, ' + IMAGE_STYLE,
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
      'Close-up of a fresh hot plate of Uzbek plov with magical swirling golden steam, glowing warm backlight, friends finally eating happily in the background, ' + IMAGE_STYLE,
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
    minSeconds: 9.5,
    transitionOut: 'fade',
    imagePrompt:
      'Split composition: on the left a friend happily eating plov with a spoon, on the right a friend photographing plov with a phone, a big question mark sticker in the middle, ' + IMAGE_STYLE,
  },
];

export const narrationOf = (scene: SceneConfig) => scene.segments.map((s) => s.text).join(' ');
