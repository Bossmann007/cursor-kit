// Render any page with window.renderAt(t) + window.TOTAL to MP4 with a virtual clock (one screenshot per frame, piped to ffmpeg).
// Same video on any machine. Needs `npm i playwright-core` next to it (or in the project) and ffmpeg; uses Brave, else Chrome.
//   node render.mjs --html social.html                       -> ~/Downloads/<html name>-video.mp4 (1080x1920)
//   node render.mjs --html slides.html --w 1920 --h 1080 --saida x.mp4
//   node render.mjs --html social.html --saida x.mp4 --de 7 --ate 13
//   node render.mjs --html social.html --quadros 2,5,10 --pasta frames   (PNGs only, for review)
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
const fps = Number(args.fps || 30), W = Number(args.w || 1080), H = Number(args.h || 1920);
if (!args.html) { console.error("Use --html <page with window.renderAt and window.TOTAL>"); process.exit(1); }
const html = path.resolve(String(args.html)), base = path.basename(html, ".html");
const exe = [args.navegador, process.env.NAVEGADOR, "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"].filter(Boolean).find(p => existsSync(p));
if (!exe) { console.error("No Chromium browser found (Brave or Chrome). Use --navegador <path>."); process.exit(1); }

const browser = await chromium.launch({ executablePath: exe, headless: true, args: ["--hide-scrollbars", "--force-color-profile=srgb"] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const errs = [];
page.on("pageerror", e => errs.push(String(e)));
page.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
await page.goto(pathToFileURL(html).href + "?render");
await page.waitForFunction(() => window.pronto === true, null, { timeout: 30000 });
const total = await page.evaluate(() => window.TOTAL);
// a @font-face that failed to load renders in the fallback font without any error: fail loudly instead
const badFonts = await page.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status !== "loaded").map(f => `${f.family} ${f.weight} ${f.style}: ${f.status}`); });
if (badFonts.length) errs.push("fonts not loaded (check the url() paths): " + badFonts.join(", "));
if (errs.length) console.warn("Page warnings:\n  " + errs.join("\n  "));

if (args.quadros) {
  const dir = path.resolve(path.dirname(html), args.pasta || "frames"); mkdirSync(dir, { recursive: true });
  for (const s of String(args.quadros).split(",").map(Number)) {
    await page.evaluate(t => window.renderAt(t), s);
    const f = path.join(dir, `t${s.toFixed(1).padStart(5, "0")}.png`);
    await page.screenshot({ path: f, type: "png" }); console.log(f);
  }
  await browser.close(); process.exit(errs.length ? 2 : 0);
}

const a = Number(args.de || 0), b = Number(args.ate || total), times = [];
for (let i = 0; a + i / fps < b - 1e-9; i++) times.push(a + i / fps);
const out = path.resolve(args.saida || path.join(os.homedir(), "Downloads", base + "-video.mp4"));
const ff = spawn("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
  "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p", "-color_range", "tv", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
  "-r", String(fps), "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
const done = new Promise((ok, bad) => ff.on("close", c => c === 0 ? ok() : bad(new Error("ffmpeg exit " + c))));
const write = buf => new Promise(ok => ff.stdin.write(buf) ? ok() : ff.stdin.once("drain", ok));
const t0 = Date.now();
for (let i = 0; i < times.length; i++) {
  await page.evaluate(t => window.renderAt(t), times[i]);
  let frame;
  for (let k = 1; ; k++) { try { frame = await page.screenshot({ type: "jpeg", quality: 95 }); break; } catch (e) { if (k >= 3) throw e; await page.waitForTimeout(500); } }
  await write(frame);
  if (i % fps === 0 || i === times.length - 1) process.stdout.write(`\r${i + 1}/${times.length} frames · ${((Date.now() - t0) / 1000).toFixed(0)} s   `);
}
ff.stdin.end(); await done; await browser.close();
console.log(`\n${out} · ${times.length} frames · ${(times.length / fps).toFixed(1)} s`);
if (errs.length) process.exit(2);
