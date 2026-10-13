// Gera os visuais (JPG 1080x1350) de um post da Central de Conteúdo, com a identidade
// "Claudio Braga · AI Consulting" (render/draw.js, render/assets, render/fonts).
// Uso: node render/render.js <post.json> <pasta-de-saida> [marca.json]
// Escreve 01.jpg, 02.jpg, ... e imprime a lista de ficheiros.
const fs = require("fs"), path = require("path");
let chromium;
for (const p of ["playwright", "/opt/npm-tools/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (e) {} }
if (!chromium) { console.error("Playwright não encontrado"); process.exit(1); }

const [, , postFile, outDir, brandFile] = process.argv;
if (!postFile || !outDir) { console.error("Uso: node render/render.js <post.json> <pasta> [marca.json]"); process.exit(1); }
const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
const brand = Object.assign({ ink: "#111111", paper: "#FFFFFF", muted: "#8A8A8A", name: "Claudio Braga", tagline: "AI Consulting",
  fontTitle: "Space Grotesk", fontBody: "Space Grotesk", fontLabel: "Syncopate" },
  brandFile ? JSON.parse(fs.readFileSync(brandFile, "utf8")) : {});
const here = __dirname;
const b64 = f => fs.readFileSync(path.join(here, f)).toString("base64");
const DRAW = fs.readFileSync(path.join(here, "draw.js"), "utf8");

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const page = await browser.newPage();
  const css = `@font-face{font-family:"Space Grotesk";src:url(data:font/ttf;base64,${b64("fonts/SpaceGrotesk.ttf")});font-weight:300 700}
@font-face{font-family:"Syncopate";src:url(data:font/ttf;base64,${b64("fonts/Syncopate-Bold.ttf")});font-weight:700}`;
  await page.setContent(`<html><head><style>${css}</style></head><body>
<canvas id="c" width="1080" height="1350"></canvas>
<img id="art" src="data:image/jpeg;base64,${b64("assets/arte.jpg")}"><img id="logo" src="data:image/jpeg;base64,${b64("assets/logo.jpg")}">
<script>${DRAW}</script></body></html>`);
  const n = Math.max(1, (post.slides || []).length);
  const files = [];
  for (let i = 0; i < n; i++) {
    const data = await page.evaluate(async ({ post, i, brand }) => {
      await Promise.all(['700 80px "Space Grotesk"', '600 40px "Space Grotesk"', '400 40px "Space Grotesk"', '500 24px "Space Grotesk"', '700 19px "Syncopate"'].map(f => document.fonts.load(f)));
      const art = document.getElementById("art"), logo = document.getElementById("logo");
      await Promise.all([art, logo].map(im => im.complete ? 0 : new Promise(r => { im.onload = r; im.onerror = r; })));
      const cv = document.getElementById("c"); drawSlideCB(cv, post, i, "pt", brand, { art, logo }); return cv.toDataURL("image/jpeg", 0.92);
    }, { post, i, brand });
    const f = path.join(outDir, String(i + 1).padStart(2, "0") + ".jpg");
    fs.writeFileSync(f, Buffer.from(data.split(",")[1], "base64")); files.push(f);
  }
  await browser.close();
  console.log(JSON.stringify(files));
})().catch(e => { console.error(e); process.exit(1); });
