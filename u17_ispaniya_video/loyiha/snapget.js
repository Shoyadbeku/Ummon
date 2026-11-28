// usage: node snapget.js <youtube_url> <out.json>
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
 const b=await chromium.launch(); const p=await b.newPage(); let data=null;
 p.on('response',async r=>{ if(r.url().includes('api.snapany.com/v1/extract')){ try{data=await r.json()}catch(e){} }});
 await p.goto('https://snapany.com/youtube',{waitUntil:'domcontentloaded',timeout:60000});
 await p.waitForTimeout(2500);
 await (await p.$('input')).fill(process.argv[2]); await p.keyboard.press('Enter');
 for(let i=0;i<60&&!data;i++) await p.waitForTimeout(500);
 fs.writeFileSync(process.argv[3],JSON.stringify(data||{error:'none'}));
 await b.close();
})();
