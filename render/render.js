// Gera os visuais (JPG 1080x1350) de um post da Central de Conteúdo.
// Uso: node render/render.js <post.json> <pasta-de-saida> [marca.json]
// post.json: {slides:[...], texts:{pt}, pilar} no formato do painel. marca.json: config/marca.brand.
// Escreve 01.jpg, 02.jpg, ... e imprime a lista de ficheiros.
const fs = require("fs"), path = require("path");
let chromium;
for (const p of ["playwright", "/opt/npm-tools/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (e) {} }
if (!chromium) { console.error("Playwright não encontrado"); process.exit(1); }

const [, , postFile, outDir, brandFile] = process.argv;
if (!postFile || !outDir) { console.error("Uso: node render/render.js <post.json> <pasta> [marca.json]"); process.exit(1); }
const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
const brand = Object.assign({ primary: "#12355B", accent: "#F2A541", ink: "#0F1B2D", paper: "#FFFFFF", name: "", fontTitle: "Archivo", fontBody: "IBM Plex Sans" },
  brandFile ? JSON.parse(fs.readFileSync(brandFile, "utf8")) : {});
const fontsDir = path.join(__dirname, "fonts");
const b64 = f => fs.readFileSync(path.join(fontsDir, f)).toString("base64");

const DRAW = String.raw`
const W=1080,H=1350,P=96;
const tr=(v,lang)=>v==null?"":(typeof v==="string"?v:(v[lang]??v.pt??v.en??""));
function font(w,size,fam,fb){ return w+" "+size+'px "'+fam+'", '+fb; }
function lines(ctx,text,maxW){ const out=[]; String(text||"").split("\n").forEach(par=>{ const words=par.split(/[ \t]+/).filter(Boolean); if(!words.length){out.push("");return;} let line=words[0]; for(let i=1;i<words.length;i++){ const t=line+" "+words[i]; if(ctx.measureText(t).width<=maxW) line=t; else {out.push(line); line=words[i];} } out.push(line); }); return out; }
function fit(ctx,text,maxW,maxLines,start,min,w,fam,fb){ let size=start,ls; for(;size>=min;size-=4){ ctx.font=font(w,size,fam,fb); ls=lines(ctx,text,maxW); if(ls.length<=maxLines) break; } return {size:Math.max(size,min),ls}; }
function block(ctx,ls,x,y,lh){ ls.forEach((l,i)=>ctx.fillText(l,x,y+i*lh)); return y+ls.length*lh; }
function spacing(ctx,v){ try{ ctx.letterSpacing=v; }catch(e){} }
function alpha(hex,a){ const h=String(hex||"#000").replace("#",""); const n=parseInt(h.length===3?h.split("").map(c=>c+c).join(""):h,16)||0; return "rgba("+(n>>16&255)+","+(n>>8&255)+","+(n&255)+","+a+")"; }
function firstLine(t){ return String(t||"").split("\n").find(l=>l.trim())||""; }
function drawSlide(cv,p,i,lang,b){
  const ctx=cv.getContext("2d"), FT=b.fontTitle||"Archivo", FB=b.fontBody||"IBM Plex Sans";
  const slides=(p.slides&&p.slides.length)?p.slides:[{kind:"frase",title:firstLine(tr(p.texts,lang))}];
  const n=slides.length, s=slides[Math.min(i,n-1)], kind=s.kind||"ponto", dark=(kind==="capa"||kind==="cta");
  const bg=dark?b.primary:b.paper, fg=dark?b.paper:b.ink, ac=b.accent, maxW=W-2*P;
  ctx.textBaseline="alphabetic"; ctx.fillStyle=bg; ctx.fillRect(0,0,W,H);
  ctx.fillStyle=ac; ctx.fillRect(P,P,64,10);
  const eb=tr(s.eyebrow,lang)||p.pilar||"";
  ctx.fillStyle=alpha(fg,dark?.75:.6); ctx.font=font(600,26,FB,"sans-serif"); spacing(ctx,"3px"); ctx.fillText(eb.toUpperCase().slice(0,48),P,P+64); spacing(ctx,"0px");
  const title=tr(s.title,lang), body=tr(s.body,lang); let y;
  if(kind==="capa"){ const f=fit(ctx,title,maxW,6,104,60,800,FT,"sans-serif"); ctx.fillStyle=fg; ctx.font=font(800,f.size,FT,"sans-serif"); y=block(ctx,f.ls,P,330,f.size*1.08);
    if(body){ ctx.font=font(400,40,FB,"sans-serif"); ctx.fillStyle=alpha(fg,.82); block(ctx,lines(ctx,body,maxW).slice(0,5),P,y+40,54); }
    if(n>1){ ctx.fillStyle=ac; ctx.font=font(600,30,FB,"sans-serif"); ctx.fillText(lang==="en"?"Swipe →":"Deslize →",P,H-190); } }
  else if(kind==="numero"){ const st=tr(s.stat,lang); const f=fit(ctx,st,maxW,1,280,120,800,FT,"sans-serif"); ctx.fillStyle=ac; ctx.font=font(800,f.size,FT,"sans-serif"); ctx.fillText(st,P-6,300+f.size*.82);
    y=300+f.size*.82+f.size*.22+70; const ft=fit(ctx,title,maxW,4,60,40,700,FT,"sans-serif"); ctx.fillStyle=fg; ctx.font=font(700,ft.size,FT,"sans-serif"); y=block(ctx,ft.ls,P,y,ft.size*1.15);
    if(body){ ctx.font=font(400,36,FB,"sans-serif"); ctx.fillStyle=alpha(fg,.78); block(ctx,lines(ctx,body,maxW).slice(0,6),P,y+28,50); }
    const src=tr(s.source,lang); if(src){ ctx.font=font(400,24,FB,"sans-serif"); ctx.fillStyle=alpha(fg,.55); block(ctx,lines(ctx,(lang==="en"?"Source: ":"Fonte: ")+src,maxW).slice(0,2),P,H-200,32); } }
  else if(kind==="frase"){ ctx.fillStyle=ac; ctx.font=font(800,220,FT,"serif"); ctx.fillText("“",P-10,420); const f=fit(ctx,title,maxW,7,80,46,700,FT,"sans-serif"); ctx.fillStyle=fg; ctx.font=font(700,f.size,FT,"sans-serif"); y=block(ctx,f.ls,P,470,f.size*1.16);
    if(body){ ctx.font=font(400,36,FB,"sans-serif"); ctx.fillStyle=alpha(fg,.7); block(ctx,lines(ctx,body,maxW).slice(0,4),P,y+36,50); } }
  else if(kind==="cta"){ const f=fit(ctx,title,maxW,5,88,52,800,FT,"sans-serif"); ctx.fillStyle=fg; ctx.font=font(800,f.size,FT,"sans-serif"); y=block(ctx,f.ls,P,360,f.size*1.1);
    if(body){ ctx.font=font(400,40,FB,"sans-serif"); ctx.fillStyle=alpha(fg,.82); y=block(ctx,lines(ctx,body,maxW).slice(0,6),P,y+44,56); } ctx.fillStyle=ac; ctx.fillRect(P,y+50,maxW*.34,8); }
  else { const idx=slides.slice(0,i+1).filter(x=>(x.kind||"ponto")==="ponto").length; ctx.fillStyle=ac; ctx.font=font(800,150,FT,"sans-serif"); ctx.fillText(String(idx).padStart(2,"0"),P-6,340);
    const f=fit(ctx,title,maxW,4,68,44,750,FT,"sans-serif"); ctx.fillStyle=fg; ctx.font=font(750,f.size,FT,"sans-serif"); y=block(ctx,f.ls,P,450,f.size*1.12);
    if(body){ ctx.font=font(400,38,FB,"sans-serif"); ctx.fillStyle=alpha(fg,.78); block(ctx,lines(ctx,body,maxW).slice(0,9),P,y+36,54); } }
  ctx.fillStyle=alpha(fg,.18); ctx.fillRect(P,H-130,maxW,2);
  ctx.fillStyle=alpha(fg,.85); ctx.font=font(700,28,FT,"sans-serif"); ctx.fillText(b.name&&b.name!=="A sua marca"?b.name:"",P,H-80);
  if(n>1){ ctx.font=font(500,26,"IBM Plex Mono","monospace"); ctx.fillStyle=alpha(fg,.55); const t=(Math.min(i,n-1)+1)+"/"+n; ctx.fillText(t,W-P-ctx.measureText(t).width,H-80); }
}`;

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const page = await browser.newPage();
  const css = `@font-face{font-family:"Archivo";src:url(data:font/ttf;base64,${b64("Archivo.ttf")});font-weight:100 900}
@font-face{font-family:"IBM Plex Sans";src:url(data:font/ttf;base64,${b64("IBMPlexSans.ttf")});font-weight:100 700}
@font-face{font-family:"IBM Plex Mono";src:url(data:font/ttf;base64,${b64("IBMPlexMono-Medium.ttf")});font-weight:500}`;
  await page.setContent(`<html><head><style>${css}</style></head><body><canvas id="c" width="1080" height="1350"></canvas><script>${DRAW}</script></body></html>`);
  const n = Math.max(1, (post.slides || []).length);
  const files = [];
  for (let i = 0; i < n; i++) {
    const data = await page.evaluate(async ({ post, i, brand }) => {
      await Promise.all(['800 80px "Archivo"', '700 40px "Archivo"', '400 40px "IBM Plex Sans"', '600 26px "IBM Plex Sans"', '500 26px "IBM Plex Mono"'].map(f => document.fonts.load(f)));
      const cv = document.getElementById("c"); drawSlide(cv, post, i, "pt", brand); return cv.toDataURL("image/jpeg", 0.92);
    }, { post, i, brand });
    const f = path.join(outDir, String(i + 1).padStart(2, "0") + ".jpg");
    fs.writeFileSync(f, Buffer.from(data.split(",")[1], "base64")); files.push(f);
  }
  await browser.close();
  console.log(JSON.stringify(files));
})().catch(e => { console.error(e); process.exit(1); });
