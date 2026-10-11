// Headless play-test driver: Ruffle in Chromium via Playwright.
// usage: node test/run.js <swf> <outdir> <scenario.json>
// steps: {"wait":ms} {"click":[x,y]} {"move":[x,y]} {"shot":"name"} {"key":"F"}
//        {"rh":["cmd",a,b]}  (debug builds: ExternalInterface hook, result logged)
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const http = require('http'); const fs = require('fs'); const path = require('path');
const [,, swfPath, outDir, stepsFile] = process.argv;
const root = __dirname;
const types = {'.html':'text/html','.js':'text/javascript','.wasm':'application/wasm','.swf':'application/x-shockwave-flash','.map':'application/json'};
const srv = http.createServer((req,res)=>{
  const u = decodeURIComponent(req.url.split('?')[0]);
  const f = u === '/game.swf' ? swfPath : path.join(root, u);
  fs.readFile(f,(e,d)=>{ if(e){res.writeHead(404);res.end();return;} res.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'}); res.end(d); });
});
srv.listen(0, async ()=>{
  const port = srv.address().port;
  const browser = await chromium.launch({ args:['--autoplay-policy=no-user-gesture-required','--use-gl=swiftshader','--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport:{width:640,height:480}, locale:'en-US' });
  const logs = [];
  page.on('console', m => { const t = m.text(); if (!/Unknown tag code|GL Driver|GPU stall/.test(t)) logs.push('[' + m.type() + '] ' + t.replace(/%c/g,'').replace(/color: [^;]*;? ?|background: #444|font-style: italic/g,'')); });
  page.on('pageerror', e => logs.push('[pageerror] ' + e));
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  fs.mkdirSync(outDir,{recursive:true});
  const steps = JSON.parse(fs.readFileSync(stepsFile,'utf8'));
  // close Ruffle's "hardware acceleration" notice when it shows up
  const dismiss = async () => page.evaluate(() => { const p = window.player; const sr = p && p.shadowRoot; if (!sr) return; sr.querySelectorAll('.hardware-acceleration-modal, #hardware-acceleration-modal, .modal').forEach(m => m.remove()); });
  for (const s of steps) {
    if (s.wait) await page.waitForTimeout(s.wait);
    await dismiss();
    if (s.click) { await page.mouse.move(s.click[0], s.click[1], {steps: 3}); await page.waitForTimeout(80); await page.mouse.down(); await page.waitForTimeout(80); await page.mouse.up(); }
    if (s.move) await page.mouse.move(s.move[0], s.move[1], {steps: s.steps || 5});
    if (s.key) { await page.keyboard.press(s.key); }
    if (s.type) { await page.keyboard.type(s.type, {delay: 50}); }
    if (s.rh) { const r = await page.evaluate(a => { try { return window.player.rh(...a); } catch (e) { return 'ERR ' + e; } }, s.rh); logs.push('[rh] ' + JSON.stringify(s.rh) + ' => ' + r); if (s.print) console.log(JSON.stringify(s.rh) + ' => ' + r); }
    if (s.shot) await page.screenshot({ path: path.join(outDir, s.shot + '.png') });
    if (s.autoplay) {
      // drives a whole run with debug shots; stops at the game-complete frame or timeout
      const rh = (...a) => page.evaluate(a => { try { return window.player.rh(...a); } catch (e) { return 'ERR ' + e; } }, a);
      const t0 = Date.now(); let lastFrame = '', shots = 0, frameSince = Date.now(), n = 0;
      while (Date.now() - t0 < s.autoplay.maxMs) {
        await page.waitForTimeout(400);
        const fr = await rh('get', '_root._currentframe');
        if (fr !== lastFrame) { logs.push(`[auto] frame ${fr} level=${await rh('get','_global.progress.level')} t=${Math.round((Date.now()-t0)/1000)}s`); lastFrame = fr; frameSince = Date.now();
          if (s.autoplay.shots) await page.screenshot({ path: path.join(outDir, `auto_${String(++n).padStart(3,'0')}_f${fr}.png`) }); }
        if (fr === '13') { logs.push('[auto] reached game complete'); break; }
        if (fr === '9') { await page.mouse.click(595, 455); continue; }
        if (fr === '11') { await page.waitForTimeout(800); await page.mouse.click(550, 380); continue; }
        if (fr === '12') { if (Date.now() - frameSince > 15000) { await page.mouse.click(320, 240); } if (Date.now() - frameSince > 25000) { logs.push('[auto] endtro stuck -> goto startLevel'); await rh('goto','startLevel'); } continue; }
        if (fr === '10') {
          if ((await rh('get','hud.mcBeginMessage')) !== 'undefined') { await page.mouse.click(320, 240); continue; }
          if ((await rh('get','hud.mcFinishMessage')) !== 'undefined') { await page.waitForTimeout(1500); await page.mouse.click(320, 240); continue; }
          if ((await rh('get','hud.hudIntructions')) !== 'undefined') { await page.mouse.click(55, 452); continue; }
          await rh('set', 'level.player1.megas', 9);
          const r = await rh('call', 'rhDbgFire', [s.autoplay.slot || 5, 0]);
          if (String(r).startsWith('fired')) { shots++; }
          if (Date.now() - frameSince > 240000) { logs.push('[auto] battle too long'); }
        }
      }
      logs.push(`[auto] done shots=${shots} elapsed=${Math.round((Date.now()-t0)/1000)}s`);
    }
  }
  fs.writeFileSync(path.join(outDir,'console.txt'), logs.join('\n'));
  await browser.close(); srv.close();
});
