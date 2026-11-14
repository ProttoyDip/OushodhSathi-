// Records the video material at 1920x1080 and stitches a silent draft cut.
//
//   cd video && npm install && node record.mjs [siteUrl]
//
// siteUrl defaults to http://localhost:3000 (run the frontend first). Needs Chrome installed.
// Writes docs/video/clips/*.webm, docs/video/stills/*.png and docs/video/draft-cut.mp4.
// The timeline below is the single source of truth; SHOTLIST.md and the captions follow it.
import ffmpeg from "@ffmpeg-installer/ffmpeg";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import puppeteer from "puppeteer-core";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../docs/video");
const SCENES = join(HERE, "scenes");
const SITE = process.argv[2] ?? "http://localhost:3000";
const CHROME = process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";

// [clip, seconds] in order. 178 s in total: under the 3:00 limit.
export const TIMELINE = [
  ["01-problem", 15],
  ["shelf", 15],          // placeholder: replace with a real photo of a consenting family's shelf
  ["02-solution", 20],
  ["landing", 10],
  ["demo", 65],           // /demo steps 2-13, one clip per step, paced by DEMO_STEPS
  ["03-architecture", 10],
  ["04-ai-approach", 15],
  ["05-families", 10],
  ["06-impact", 10],
  ["07-close", 8],        // ends on the passport card, not a logo
];
// seconds on each /demo step, from step 2 (Scan) to step 13 (Doctor visit)
export const DEMO_STEPS = [
  ["Scan", 4], ["The list", 5], ["Duplicate", 7], ["Review", 6], ["Family", 5], ["Passport", 6],
  ["Emergency", 5], ["Today", 6], ["Report", 4], ["Sathi", 5], ["Ask a person", 6], ["Doctor visit", 6],
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const demoClip = (i) => `demo-${String(i + 2).padStart(2, "0")}-${DEMO_STEPS[i][0].toLowerCase().replace(/\s+/g, "-")}`;
mkdirSync(join(OUT, "clips"), { recursive: true });
mkdirSync(join(OUT, "stills"), { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--window-size=1920,1080", "--hide-scrollbars"],
  defaultViewport: { width: 1920, height: 1080 },
});

async function fresh(locale = "en") {
  const p = await browser.newPage();
  await p.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
  await p.setCookie({ name: "locale", value: locale, domain: new URL(SITE).hostname, path: "/" });
  return p;
}

/** Records a page for `seconds` plus a margin. The screen recorder can fall behind real time on
 * heavy pages, so every clip runs long and the draft cut trims it to its exact slot. */
const MARGIN = 2.5;
async function record(p, name, seconds) {
  const path = join(OUT, "clips", `${name}.webm`);
  const rec = await p.screencast({ path, ffmpegPath: ffmpeg.path });
  await sleep((seconds + MARGIN) * 1000);
  await rec.stop();
  console.log("recorded", name);
}

async function scene(name, seconds) {
  const p = await fresh();
  // load hidden, then re-trigger the entrance so the recording starts on the first frame
  await p.goto(pathToFileURL(join(SCENES, `${name}.html`)).href, { waitUntil: "networkidle0" });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: join(OUT, "stills", `${name}.png`) });
  await p.evaluate(() => {
    const main = document.querySelector("main");
    main.replaceWith(main.cloneNode(true));
  });
  await record(p, name, seconds);
  await p.close();
}

for (const [name, seconds] of TIMELINE) {
  if (/^\d\d-/.test(name)) {
    await scene(name, seconds);
  } else if (name === "shelf") {
    const p = await fresh();
    await p.goto(`${SITE}/demo?step=0`, { waitUntil: "networkidle0" });
    await sleep(500);
    await p.goto(`${SITE}/demo?step=0`, { waitUntil: "domcontentloaded" });
    await record(p, name, seconds);
    await p.close();
  } else if (name === "landing") {
    const p = await fresh();
    await p.goto(SITE, { waitUntil: "networkidle0" });
    await sleep(800);
    await p.goto(SITE, { waitUntil: "domcontentloaded" });
    await record(p, name, seconds);
    await p.close();
  } else if (name === "demo") {
    // one clip per step, each opened fresh so its entrance plays from the first frame
    for (const [i, [, s]] of DEMO_STEPS.entries()) {
      const p = await fresh();
      const url = `${SITE}/demo?step=${i + 1}`;
      await p.goto(url, { waitUntil: "networkidle0" });
      await sleep(400);
      await p.goto(url, { waitUntil: "domcontentloaded" });
      await record(p, demoClip(i), s);
      await sleep(Math.min(s, 3) * 1000);
      await p.screenshot({ path: join(OUT, "stills", `${demoClip(i)}.png`) });
      await p.close();
    }
  }
}
await browser.close();

// silent draft cut: every clip trimmed to its slot, scaled to 1920x1080 at 30 fps, H.264
const CUT = TIMELINE.flatMap(([name, s]) => (name === "demo" ? DEMO_STEPS.map(([, ds], i) => [demoClip(i), ds]) : [[name, s]]));
const inputs = CUT.flatMap(([name]) => ["-i", join(OUT, "clips", `${name}.webm`)]);
const parts = CUT.map(([, s], i) =>
  `[${i}:v]trim=0:${s},setpts=PTS-STARTPTS,fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf3f5f9,setsar=1[v${i}]`);
const filter = `${parts.join(";")};${CUT.map((_, i) => `[v${i}]`).join("")}concat=n=${CUT.length}:v=1:a=0[out]`;
const draft = join(OUT, "draft-cut.mp4");
if (CUT.every(([name]) => existsSync(join(OUT, "clips", `${name}.webm`)))) {
  execFileSync(ffmpeg.path, ["-y", "-loglevel", "error", ...inputs, "-filter_complex", filter, "-map", "[out]",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-movflags", "+faststart", draft]);
  console.log("draft cut:", draft);
}
