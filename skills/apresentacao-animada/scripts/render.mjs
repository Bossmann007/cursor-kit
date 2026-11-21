// Render any page with window.renderAt(t) + window.TOTAL to MP4 with a virtual clock (one screenshot per frame, piped to ffmpeg).
// Same video on any machine. Needs `npm i playwright-core@1.65.1` next to it (or in the project) and ffmpeg; uses --navegador, NAVEGADOR, Brave, Chrome or Chromium.
// Output is H.264 yuv420p tagged BT.709 (primaries, transfer, matrix) in TV range.
// Refuses to replace an existing output MP4 unless --sobrescrever is given.
//   node render.mjs --html social.html                       -> ~/Downloads/<html name>-video.mp4 (1080x1920)
//   node render.mjs --html slides.html --w 1920 --h 1080 --saida x.mp4
//   node render.mjs --html social.html --saida x.mp4 --de 7 --ate 13
//   node render.mjs --html social.html --quadros 2,5,10 --pasta frames   (PNGs only, for review)
//   node render.mjs --html social.html --leitura             (reading-time check of window.TEXTS only; exit 3 on a short text)
//   node render.mjs --html anim.html --relogio [--duracao 6] (page animated by GSAP, CSS or rAF, no renderAt: virtual clock)
// Exit codes: 0 ok, 1 usage or setup error, 2 page error or @font-face not loaded, 3 reading-time violation (wins over 2).
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, xs) => {
  if (a.startsWith("--")) acc.push([a.slice(2), xs[i + 1] && !xs[i + 1].startsWith("--") ? xs[i + 1] : true]);
  return acc;
}, []));
const fps = Number(args.fps || 30), W = Number(args.w || 1080), H = Number(args.h || 1920), clock = Boolean(args.relogio);
if (!args.html) { console.error("Use --html <page with window.renderAt and window.TOTAL>"); process.exit(1); }
if (args.duracao !== undefined && !(typeof args.duracao === "string" && Number.isFinite(Number(args.duracao)) && Number(args.duracao) > 0)) { console.error("--duracao needs a number of seconds, e.g. --duracao 6"); process.exit(1); }
const html = path.resolve(String(args.html)), base = path.basename(html, ".html");
const out = path.resolve(args.saida || path.join(os.homedir(), "Downloads", base + "-video.mp4"));
if (!args.quadros && !args.leitura && existsSync(out) && !args.sobrescrever) { console.error(`${out} already exists. Use --saida <other file> or --sobrescrever.`); process.exit(1); }
const exe = [args.navegador, process.env.NAVEGADOR, "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium"].filter(Boolean).find(p => existsSync(p));
if (!exe) { console.error("No Chromium browser found (Brave, Chrome or Chromium). Use --navegador <path> or NAVEGADOR=<path>."); process.exit(1); }

// Virtual clock for pages without renderAt (idea from https://awesomeclaude.ai/claude-video; site footer: MIT, repository LICENSE: CC0 1.0; written from scratch).
// Time stands still until __clock.tick(t): it runs the queued rAF callbacks at t and pauses every CSS/Web Animation at
// its own age (t minus the time it was first seen). setTimeout/setInterval are not virtualized, and paused animations never
// fire finished/animationend (chain scenes by time, not by those events). new Date() stays real time; iframes and
// scroll-driven animations are not driven. The page's animation rate is set to 0 over CDP before loading (and the
// Animation domain stays enabled: disabling it resets the rate), so no CSS animation runs or ends before the first tick.
function installClock() {
  let now = 0, queue = [], nextId = 1, cancelled = new Set();
  const epoch = Date.UTC(2026, 0, 1), born = new WeakMap();
  performance.now = () => now;
  Date.now = () => epoch + now;
  window.requestAnimationFrame = cb => { queue.push([nextId, cb]); return nextId++; };
  window.cancelAnimationFrame = id => { queue = queue.filter(([i]) => i !== id); cancelled.add(id); };
  window.__clock = { tick(t) {
    now = t * 1000;
    const run = queue; queue = [];
    for (const [id, cb] of run) if (!cancelled.has(id)) try { cb(now); } catch (e) { console.error("rAF callback: " + (e && e.stack || e)); }
    cancelled.clear();
    for (const a of document.getAnimations()) {
      if (a.timeline !== document.timeline) continue;
      if (!born.has(a)) born.set(a, now);
      a.pause(); a.currentTime = now - born.get(a);
    }
  } };
}

const browser = await chromium.launch({ executablePath: exe, headless: true, args: ["--hide-scrollbars", "--force-color-profile=srgb"] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", e => errs.push(String(e)));
page.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
if (clock) {
  await page.addInitScript(installClock);
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Animation.enable"); await cdp.send("Animation.setPlaybackRate", { playbackRate: 0 });
}
await page.goto(pathToFileURL(html).href + "?render", { waitUntil: "load" });
// polling by interval: the default rAF polling would wait on the virtual clock forever. With --relogio, a page with async
// setup starts with window.pronto = false and sets it true when ready; a page without pronto starts at load.
await page.waitForFunction(c => c ? window.pronto !== false : window.pronto === true, clock, { timeout: 30000, polling: 100 });
const total = Number(args.duracao) || await page.evaluate(() => window.TOTAL);
if (!(Number.isFinite(total) && total > 0)) { console.error("No duration: set window.TOTAL (seconds) in the page or pass --duracao <s>."); await browser.close(); process.exit(1); }
// a @font-face that failed to load renders in the fallback font without any error: fail loudly instead
const badFonts = await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status !== "loaded").map(f => `${f.family} ${f.weight} ${f.style}: ${f.status}`); });
if (badFonts.length) errs.push("fonts not loaded (check the url() paths): " + badFonts.join(", "));
if (errs.length) console.warn("Page warnings:\n  " + errs.join("\n  "));
const shown = errs.length, late = () => { if (errs.length > shown) console.warn("Page warnings while drawing:\n  " + errs.slice(shown).join("\n  ")); };

// renderAt jumps to any t; the virtual clock only moves forward, one frame at a time, so rAF loops see every step
// (times are sorted before drawing).
let clockFrame = -1;
async function draw(t) {
  if (!clock) return page.evaluate(t => window.renderAt(t), t);
  const target = Math.round(t * fps); // snaps to the nearest frame
  for (let i = clockFrame + 1; i <= target; i++) await page.evaluate(s => window.__clock.tick(s), i / fps);
  clockFrame = Math.max(clockFrame, target);
}

// Reading time (rule: every text stays at least chars/15 + 1.5 s; a title at least 4 s, a subtitle at least 1.8 s).
// window.TEXTS is either a function t -> [{text, kind}] or a list [{text, kind, from, to}]; kind is title, subtitle or text.
if (args.leitura) {
  const floor = { title: 4, subtitle: 1.8, text: 0 };
  const frames = await page.evaluate(([n, f]) => {
    const T = window.TEXTS;
    if (typeof T !== "function" && !Array.isArray(T)) return null;
    if (Array.isArray(T) && T.some(x => !x || !Number.isFinite(x.from) || !Number.isFinite(x.to) || x.from < 0 || x.to <= x.from || x.from >= n / f)) return "fromto";
    const at = t => [].concat((typeof T === "function" ? T(t) : T.filter(x => t >= x.from && t < x.to)) ?? []).filter(Boolean);
    return Array.from({ length: n }, (_, i) => at(i / f).map(x => typeof x === "string" ? { text: x, kind: "text" } : x));
  }, [Math.round(total * fps), fps]);
  if (frames === "fromto") { console.error("--leitura: every item of the window.TEXTS list needs numeric from < to (seconds), starting inside the video."); await browser.close(); process.exit(1); }
  if (!frames) { console.error("--leitura needs window.TEXTS: a function t -> [{text, kind}] or a list [{text, kind, from, to}]."); await browser.close(); process.exit(1); }
  const unknown = [...new Set(frames.flat().map(x => x.kind || "text"))].filter(k => !Object.hasOwn(floor, k));
  if (unknown.length) { console.error(`--leitura: unknown kind ${unknown.join(", ")}; use title, subtitle or text.`); await browser.close(); process.exit(1); }
  const open = new Map(), runs = [];
  const close = (key, end) => { const [kind, text] = JSON.parse(key); runs.push({ kind, text, from: open.get(key), end }); open.delete(key); };
  frames.forEach((list, i) => {
    const now = new Set(list.map(x => JSON.stringify([x.kind || "text", String(x.text).replace(/\s+/g, " ").trim()])));
    for (const key of [...open.keys()]) if (!now.has(key)) close(key, i);
    for (const key of now) if (!open.has(key)) open.set(key, i);
  });
  for (const key of [...open.keys()]) close(key, frames.length);
  let bad = 0;
  for (const r of runs) {
    const onScreen = (r.end - r.from) / fps, need = Math.max(floor[r.kind] ?? 0, [...r.text].length / 15 + 1.5);
    if (onScreen + 1 / fps < need) { bad++; console.log(`SHORT ${r.kind} t=${(r.from / fps).toFixed(2)}-${(r.end / fps).toFixed(2)} s: on screen ${onScreen.toFixed(2)} s, needs ${need.toFixed(2)} s: "${r.text}"`); }
  }
  console.log(bad ? `${bad} of ${runs.length} texts too short to read` : `reading time OK: ${runs.length} texts`);
  late(); await browser.close(); process.exit(bad ? 3 : errs.length ? 2 : 0);
}

if (args.quadros) {
  const raw = String(args.quadros).split(","), list = raw.map(Number);
  if (raw.some(x => x.trim() === "") || !list.every(x => Number.isFinite(x) && x >= 0)) { console.error("--quadros needs seconds separated by commas, e.g. --quadros 2,5.5,9"); await browser.close(); process.exit(1); }
  const dir = path.resolve(path.dirname(html), args.pasta || "frames"); mkdirSync(dir, { recursive: true });
  for (const s of list.sort((x, y) => x - y)) {
    await draw(s);
    const shot = clock ? Math.round(s * fps) / fps : s; // name the frame the clock really drew
    const f = path.join(dir, `t${shot.toFixed(2).padStart(6, "0")}.png`);
    await page.screenshot({ path: f, type: "png" }); console.log(f);
  }
  late(); await browser.close(); process.exit(errs.length ? 2 : 0);
}

const a = Number(args.de || 0), b = Number(args.ate || total), times = [];
for (let i = 0; a + i / fps < b - 1e-9; i++) times.push(a + i / fps);
// Chrome's JPEG frames are full-range BT.601: convert the matrix and the range, then tag the stream BT.709
const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
  "-vf", "scale=in_range=pc:in_color_matrix=bt601:out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709",
  "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
  "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", String(fps), "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
const done = new Promise((ok, bad) => ff.on("close", c => c === 0 ? ok() : bad(new Error("ffmpeg exit " + c))));
const write = buf => new Promise(ok => ff.stdin.write(buf) ? ok() : ff.stdin.once("drain", ok));
const t0 = Date.now();
for (let i = 0; i < times.length; i++) {
  await draw(times[i]);
  let frame;
  for (let k = 1; ; k++) { try { frame = await page.screenshot({ type: "jpeg", quality: 95 }); break; } catch (e) { if (k >= 3) throw e; await page.waitForTimeout(500); } }
  await write(frame);
  if (i % fps === 0 || i === times.length - 1) process.stdout.write(`\r${i + 1}/${times.length} frames · ${((Date.now() - t0) / 1000).toFixed(0)} s   `);
}
ff.stdin.end(); await done; await browser.close();
console.log(`\n${out} · ${times.length} frames · ${(times.length / fps).toFixed(1)} s`);
late(); if (errs.length) process.exit(2);
