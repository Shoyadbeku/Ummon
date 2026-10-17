// Whisper nutqni tanish (brauzerda, transformers.js orqali). Audio hech qayerga yuborilmaydi;
// faqat model fayllari bir marta Hugging Face'dan yuklanib, brauzer keshida saqlanadi.
import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.5.1';

env.allowLocalModels = false;

let asr = null;
let currentModel = null;

const progress = (p) => self.postMessage({ type: 'progress', p });

async function load(model) {
  if (asr && currentModel === model) return asr;
  const hasGPU = typeof navigator !== 'undefined' && 'gpu' in navigator && (await navigator.gpu.requestAdapter().catch(() => null));
  if (hasGPU) {
    try {
      self.postMessage({ type: 'status', text: 'Model yuklanmoqda (WebGPU)…' });
      asr = await pipeline('automatic-speech-recognition', model, {
        device: 'webgpu',
        dtype: { encoder_model: 'fp32', decoder_model_merged: 'q4' },
        progress_callback: progress,
      });
      currentModel = model;
      return asr;
    } catch (e) {
      console.warn('WebGPU ishlamadi, WASM ga o‘tilmoqda', e);
    }
  }
  self.postMessage({ type: 'status', text: 'Model yuklanmoqda…' });
  asr = await pipeline('automatic-speech-recognition', model, { dtype: 'q8', progress_callback: progress });
  currentModel = model;
  return asr;
}

self.onmessage = async (e) => {
  const { audio, model } = e.data;
  try {
    const run = await load(model);
    self.postMessage({ type: 'status', text: 'Nutq matnga aylantirilmoqda…' });
    const out = await run(audio, {
      language: 'uzbek',
      task: 'transcribe',
      chunk_length_s: 30,
      stride_length_s: 5,
      return_timestamps: true,
    });
    self.postMessage({ type: 'done', out });
  } catch (err) {
    self.postMessage({ type: 'error', message: String((err && err.message) || err) });
  }
};
