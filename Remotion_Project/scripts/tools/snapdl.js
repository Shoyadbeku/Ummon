// usage: node snapdl.js <youtube_url> <out_path>
// snapyt.app workflow: paste link -> video-preview page -> pick best quality -> save file.
// Prefers the HD "merge" (video-only <=1080p avc1 + best m4a); falls back to the best ready video+audio option.
const { chromium } = require('playwright');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const ctx = await b.newContext({ acceptDownloads: true });
  const p = await ctx.newPage();
  ctx.on('page', np => { if (np !== p) np.close().catch(() => {}); }); // close ad popups
  await p.goto('https://snapyt.app/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.fill('#video-url', url);
  await p.keyboard.press('Enter');
  await p.waitForURL(/video-preview/, { timeout: 90000 });
  await p.waitForSelector('#fmt-select', { timeout: 90000 });
  await p.waitForTimeout(2000);

  const mux = await p.evaluate(() => {
    const v = [...document.querySelectorAll('#mux-video option')].filter(o => o.value)
      .map(o => ({ v: o.value, h: parseInt((o.textContent.match(/(\d+)p/)||[0,0])[1]), codec: o.dataset.codec || '', t: o.textContent.trim() }))
      .filter(o => o.h <= 1080).sort((a, b) => (b.h - a.h) || ((b.codec.startsWith('avc') ? 1 : 0) - (a.codec.startsWith('avc') ? 1 : 0)));
    const a = [...document.querySelectorAll('#mux-audio option, select[id*=audio] option')].filter(o => o.value)
      .map(o => ({ v: o.value, k: parseInt((o.textContent.match(/(\d+)\s*kbps/) || [0, 0])[1]), t: o.textContent.trim() }))
      .sort((x, y) => y.k - x.k);
    const audioSel = document.querySelector('#mux-audio') ? '#mux-audio' : (document.querySelector('select[id*=audio]') ? '#' + document.querySelector('select[id*=audio]').id : null);
    return { video: v[0] || null, audio: a[0] || null, audioSel };
  });
  const ready = await p.evaluate(() => {
    const o = [...document.querySelectorAll('#fmt-select option')].filter(o => o.dataset.kind === 'video+audio' && o.dataset.force)
      .map(o => ({ h: parseInt((o.textContent.match(/(\d+)p/)||[0,0])[1]), t: o.textContent.trim(), force: o.dataset.force }))
      .sort((a, b) => b.h - a.h);
    return o[0] || null;
  });
  console.log('AUDIOSEL', mux.audioSel); console.log('READY', ready && ready.t, '| MUX', mux.video && mux.video.t, '+', mux.audio && mux.audio.t);

  let saved = false;
  if (mux.video && mux.audio && mux.audioSel && (!ready || mux.video.h > ready.h)) {
    try {
      await p.selectOption('#mux-video', mux.video.v);
      await p.selectOption(mux.audioSel, mux.audio.v);
      const [dl] = await Promise.all([
        p.waitForEvent('download', { timeout: 300000 }),
        p.click('#merge-link'),
      ]);
      await dl.saveAs(out); saved = true; console.log('SAVED_MERGE', mux.video.t);
    } catch (e) { console.log('MERGE_FAIL', e.message.split('\n')[0]); }
  }
  if (!saved && ready) {
    const r = await ctx.request.get(ready.force, { timeout: 300000 });
    const buf = await r.body();
    require('fs').writeFileSync(out, buf);
    console.log('SAVED_READY', ready.t, r.status(), buf.length);
    saved = buf.length > 10000;
  }
  await b.close();
  process.exit(saved ? 0 : 1);
})().catch(e => { console.log('FAIL', e.message.split('\n')[0]); process.exit(1); });
