// Gera as imagens de um post da Koobings a partir dos "slides" (o mesmo desenho do painel).
// Uso: node koobings/_tools/render.js <post.json> <pasta>   → 01.jpg, 02.jpg, … (1080x1350)
const fs = require("fs"), path = require("path");
let chromium;
for (const p of ["playwright", "/opt/npm-tools/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (e) {} }
if (!chromium) { console.error("Playwright não encontrado"); process.exit(1); }
const [, , postFile, outDir] = process.argv;
const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
const slides = post.slides || [];
if (!slides.length) { console.error("O post não tem slides"); process.exit(1); }
const draw = fs.readFileSync(path.join(__dirname, "draw.js"), "utf8");
const inter = fs.readFileSync(path.join(__dirname, "Inter.ttf")).toString("base64");
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const pg = await b.newPage();
  await pg.setContent(`<html><head><style>@font-face{font-family:"Inter";src:url(data:font/ttf;base64,${inter});font-weight:100 900}</style></head><body><canvas id="c" width="1080" height="1350"></canvas><script>${draw}</script></body></html>`);
  await pg.evaluate(async () => { await Promise.all(["400 40px Inter","600 26px Inter","700 40px Inter","750 60px Inter","800 100px Inter"].map(f => document.fonts.load(f))); });
  const files = [];
  for (let i = 0; i < slides.length; i++) {
    const data = await pg.evaluate(({ slides, i }) => { const cv = document.getElementById("c"); cv.getContext("2d").clearRect(0, 0, 1080, 1350); drawSlide(cv, slides, i, {}); return cv.toDataURL("image/jpeg", 0.92); }, { slides, i });
    const f = path.join(outDir, String(i + 1).padStart(2, "0") + ".jpg"); fs.writeFileSync(f, Buffer.from(data.split(",")[1], "base64")); files.push(f);
  }
  await b.close(); console.log(JSON.stringify(files));
})().catch(e => { console.error(e); process.exit(1); });
