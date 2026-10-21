// Gera os visuais de um post da Central de Conteúdo com a identidade "Claudio Braga · hanuman.work"
// (render/draw.js, render/assets, render/fonts).
// Uso: node render/render.js <post.json> <pasta-de-saida> [marca.json]
//  - carrossel/imagem: 01.jpg, 02.jpg, ... (1080x1350)
//  - story: 01.jpg (1080x1920)
//  - reel: reel.mp4 (1080x1920, 24 fps, com faixa de áudio silenciosa) + capa.jpg
// Imprime a lista de ficheiros criados (JSON).
const fs = require("fs"), path = require("path"), os = require("os"), { execFileSync } = require("child_process");
let chromium;
for (const p of ["playwright", "/opt/npm-tools/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (e) {} }
if (!chromium) { console.error("Playwright não encontrado"); process.exit(1); }

const [, , postFile, outDir, brandFile] = process.argv;
if (!postFile || !outDir) { console.error("Uso: node render/render.js <post.json> <pasta> [marca.json]"); process.exit(1); }
const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
const brand = Object.assign({ ink: "#14161A", paper: "#F5F2EC", muted: "#6E6A64", accent: "#E4572E", name: "Claudio Braga", site: "hanuman.work",
  fontTitle: "Archivo", fontBody: "IBM Plex Sans", fontLabel: "IBM Plex Mono" },
  brandFile ? JSON.parse(fs.readFileSync(brandFile, "utf8")) : {});
const here = __dirname;
const b64 = f => fs.readFileSync(path.join(here, f)).toString("base64");
const DRAW = fs.readFileSync(path.join(here, "draw.js"), "utf8");
const fmt = post.format || "carrossel";
const tall = fmt === "reel" || fmt === "story";
const W = 1080, H = tall ? 1920 : 1350, FPS = 24;

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const page = await browser.newPage();
  const css = `@font-face{font-family:"Archivo";src:url(data:font/ttf;base64,${b64("fonts/Archivo.ttf")});font-weight:100 900}
@font-face{font-family:"IBM Plex Sans";src:url(data:font/ttf;base64,${b64("fonts/IBMPlexSans.ttf")});font-weight:100 700}
@font-face{font-family:"IBM Plex Mono";src:url(data:font/ttf;base64,${b64("fonts/IBMPlexMono-Medium.ttf")});font-weight:400 500}
@font-face{font-family:"Space Grotesk";src:url(data:font/ttf;base64,${b64("fonts/SpaceGrotesk.ttf")});font-weight:300 700}
@font-face{font-family:"Syncopate";src:url(data:font/ttf;base64,${b64("fonts/Syncopate-Bold.ttf")});font-weight:700}`;
  await page.setContent(`<html><head><style>${css}</style></head><body>
<canvas id="c" width="${W}" height="${H}"></canvas>
<img id="art" src="data:image/jpeg;base64,${b64("assets/arte.jpg")}"><img id="logo" src="data:image/jpeg;base64,${b64("assets/logo.jpg")}">
<script>${DRAW}
window.ready=(async()=>{ await Promise.all(['800 80px "Archivo"','700 40px "Archivo"','400 40px "IBM Plex Sans"','600 24px "IBM Plex Sans"','500 22px "IBM Plex Mono"'].map(f=>document.fonts.load(f)));
  const ims=[document.getElementById("art"),document.getElementById("logo")]; await Promise.all(ims.map(im=>im.complete?0:new Promise(r=>{im.onload=r;im.onerror=r;}))); })();
window.IMGS=()=>({art:document.getElementById("art"),logo:document.getElementById("logo")});
window.still=(post,i,brand)=>{ const cv=document.getElementById("c"); drawSlideCB(cv,post,i,"pt",brand,IMGS()); return cv.toDataURL("image/jpeg",0.92); };
window.TXT={};
window.frame=(post,i,brand,t,tScene,prevI,tPrev)=>{ // t: tempo total (s), tScene: tempo desde o início da cena (s)
  const cv=document.getElementById("c"), ctx=cv.getContext("2d");
  const txt=k=>{ if(!TXT[k]){ const o=document.createElement("canvas"); o.width=cv.width; o.height=cv.height; drawSlideCB(o,post,k,"pt",brand,IMGS(),{layer:"text"}); TXT[k]=o; } return TXT[k]; };
  drawSlideCB(cv,post,i,"pt",brand,IMGS(),{layer:"bg",drift:t});
  const e=x=>1-Math.pow(1-Math.min(1,Math.max(0,x)),3);
  if(prevI!=null&&tPrev<0.35){ ctx.globalAlpha=1-e(tPrev/0.35); ctx.drawImage(txt(prevI),0,-30*e(tPrev/0.35)); }
  const a=i===0?e(tScene/0.25):e((tScene-0.15)/0.5); ctx.globalAlpha=a; ctx.drawImage(txt(i),0,40*(1-a)); ctx.globalAlpha=1;
  return cv.toDataURL("image/jpeg",0.9); };
</script></body></html>`);
  await page.evaluate(() => window.ready);
  const files = [];
  const save = (f, data) => { fs.writeFileSync(f, Buffer.from(data.split(",")[1], "base64")); files.push(f); };
  if (fmt !== "reel") {
    const n = fmt === "story" ? 1 : Math.max(1, (post.slides || []).length);
    for (let i = 0; i < n; i++) save(path.join(outDir, String(i + 1).padStart(2, "0") + ".jpg"), await page.evaluate(({ post, i, brand }) => still(post, i, brand), { post, i, brand }));
  } else {
    const slides = (post.slides && post.slides.length) ? post.slides : [{ kind: "frase", title: String((post.texts && post.texts.pt) || "").split("\n")[0] }];
    const txtOf = s => ["title", "body", "stat"].map(k => s[k] == null ? "" : (typeof s[k] === "string" ? s[k] : (s[k].pt || ""))).join(" ");
    const durs = slides.map((s, k) => { const w = txtOf(s).split(/\s+/).filter(Boolean).length; return Math.min(4.6, Math.max(k === 0 ? 2.6 : 2.4, 1.2 + w * 0.24)); });
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "reel-"));
    let fno = 0, t0 = 0;
    for (let i = 0; i < slides.length; i++) {
      const nF = Math.round(durs[i] * FPS);
      for (let f = 0; f < nF; f++) {
        const ts = f / FPS, t = t0 + ts;
        const data = await page.evaluate(({ post, i, brand, t, ts }) => frame(post, i, brand, t, ts, i > 0 ? i - 1 : null, ts), { post: { ...post, slides }, i, brand, t, ts });
        fs.writeFileSync(path.join(tmp, String(fno++).padStart(5, "0") + ".jpg"), Buffer.from(data.split(",")[1], "base64"));
      }
      t0 += durs[i];
    }
    save(path.join(outDir, "capa.jpg"), await page.evaluate(({ post, brand }) => still(post, 0, brand), { post: { ...post, slides }, brand }));
    const mp4 = path.join(outDir, "reel.mp4");
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", path.join(tmp, "%05d.jpg"),
      "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", mp4]);
    fs.rmSync(tmp, { recursive: true, force: true });
    files.push(mp4);
  }
  await browser.close();
  console.log(JSON.stringify(files));
})().catch(e => { console.error(e); process.exit(1); });
