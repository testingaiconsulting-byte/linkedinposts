// Visual "Claudio Braga · hanuman.work" — alinhado com o site hanuman.work:
// etiqueta de secção em mono ("PILAR / 02"), secções numeradas 01–05, caixa "Em resumo",
// motivo dos 5 níveis de maturidade, assinatura hanuman.work e apelo ao Diagnóstico Grátis.
// drawSlideCB(canvas, post, indiceDoSlide, lingua, marca, imagens, opcoes{layer,drift})
// Tipos de slide: capa, ponto, numero, frase, resumo, cta. 1080x1350 (feed) e 1080x1920 (reel/story).
// opcoes.layer: "bg" (fundo e rodapé), "text" (só o texto) ou nada (tudo). opcoes.drift: segundos (anima o motivo).
function drawSlideCB(cv,p,i,lang,b,imgs,opts){
  opts=opts||{}; b=b||{};
  const W=cv.width,H=cv.height,P=88,maxW=W-2*P;
  const tall=H>1700, T=tall?230:0, FY=tall?H-420:H-128;
  const ctx=cv.getContext("2d");
  const ink=b.ink||"#14161A", paper=b.paper||"#F5F2EC", mute=b.muted||"#6E6A64", acc=b.accent||"#E4572E",
        dark=b.dark||ink, soft=b.soft||"#ECE7DE", line=b.line||"#D8D2C7";
  const FT=b.fontTitle||"Archivo", FB=b.fontBody||"IBM Plex Sans", FL=b.fontLabel||"IBM Plex Mono";
  const tr=(v,l)=>v==null?"":(typeof v==="string"?v:(v[l]??v.pt??v.en??""));
  const font=(w,s,f)=>w+" "+s+'px "'+f+'", sans-serif';
  const lines=(text,mw)=>{ const out=[]; String(text||"").split("\n").forEach(par=>{ const ws=par.split(/[ \t]+/).filter(Boolean); if(!ws.length){out.push("");return;} let ln=ws[0]; for(let k=1;k<ws.length;k++){ const t=ln+" "+ws[k]; if(ctx.measureText(t).width<=mw) ln=t; else {out.push(ln); ln=ws[k];} } out.push(ln); }); return out; };
  const fit=(text,mw,maxL,start,min,w,f)=>{ let s=start,ls; for(;s>=min;s-=4){ ctx.font=font(w,s,f); ls=lines(text,mw); if(ls.length<=maxL) break; } return {size:Math.max(s,min),ls}; };
  const block=(ls,x,y,lh)=>{ ls.forEach((l,k)=>ctx.fillText(l,x,y+k*lh)); return y+ls.length*lh; };
  const sp=v=>{ try{ ctx.letterSpacing=v; }catch(e){} };
  const alpha=(hex,a)=>{ const h=String(hex).replace("#",""); const n=parseInt(h.length===3?h.split("").map(c=>c+c).join(""):h,16)||0; return "rgba("+(n>>16&255)+","+(n>>8&255)+","+(n&255)+","+a+")"; };
  const rr=(x,y,w,h,r)=>{ ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); };
  const first=t=>String(t||"").split("\n").find(l=>l.trim())||"";
  const slides=(p.slides&&p.slides.length)?p.slides:[{kind:"frase",title:first(tr(p.texts,lang))}];
  const n=slides.length, idx=Math.min(i,n-1), s=slides[idx], kind=s.kind||"ponto";
  const title=tr(s.title,lang), body=tr(s.body,lang);
  const onDark=kind==="cta"; const fg=onDark?paper:ink, fgMute=onDark?alpha(paper,.7):alpha(ink,.7);
  const site=b.site||"hanuman.work", person=b.name||"Claudio Braga";
  ctx.textBaseline="alphabetic";

  // motivo: 5 níveis de maturidade (barras a subir), discreto
  const levels=(x0,yBase,wTot,hMax,col,a,d)=>{ const bw=wTot/5-14; for(let k=0;k<5;k++){ const h=hMax*(0.28+0.18*k)*(1+0.03*Math.sin((d||0)*0.6+k));
      ctx.fillStyle=k===4?alpha(acc,a*1.6>1?1:a*1.6):alpha(col,a); rr(x0+k*(bw+14),yBase-h,bw,h,6); ctx.fill(); } };

  if(opts.layer!=="text"){
    ctx.fillStyle=onDark?dark:paper; ctx.fillRect(0,0,W,H);
    // cabeçalho: wordmark + etiqueta
    ctx.fillStyle=fg; ctx.font=font(800,30,FT); sp("-0.5px"); ctx.fillText(site.replace(/\..*$/,""),P,T+92);
    const wm=ctx.measureText(site.replace(/\..*$/,"")).width; ctx.fillStyle=acc; ctx.fillText(site.slice(site.indexOf(".")>0?site.indexOf("."):site.length),P+wm,T+92); sp("0px");
    ctx.fillStyle=onDark?alpha(paper,.25):line; ctx.fillRect(P,T+122,maxW,2);
    if(kind==="capa"||kind==="cta") levels(W-P-300,tall?FY-60:FY-56,300,tall?520:340,onDark?paper:ink,onDark?.10:.07,opts.drift);
    // rodapé
    ctx.fillStyle=onDark?alpha(paper,.25):line; ctx.fillRect(P,FY,maxW,2);
    ctx.font=font(600,24,FB); ctx.fillStyle=fg; ctx.fillText(person,P,FY+56);
    const pw=ctx.measureText(person).width; ctx.font=font(400,24,FB); ctx.fillStyle=onDark?alpha(paper,.6):mute; ctx.fillText("  ·  "+(b.tagline||"Consultor de IA, "+site),P+pw,FY+56);
    if(n>1&&!tall){ ctx.font=font(500,22,FL); ctx.fillStyle=onDark?alpha(paper,.6):mute; const t=String(idx+1).padStart(2,"0")+" / "+String(n).padStart(2,"0"); ctx.fillText(t,W-P-ctx.measureText(t).width,FY+56); }
  }
  if(opts.layer==="bg") return;

  // etiqueta de secção estilo site: "PILAR / 02"
  const pts=slides.slice(0,idx+1).filter(x=>(x.kind||"ponto")==="ponto").length;
  const eb=(tr(s.eyebrow,lang)||p.pilar||"").toUpperCase().slice(0,34);
  const tag=eb+(kind==="ponto"?"  /  "+String(pts).padStart(2,"0"):"");
  ctx.font=font(500,21,FL); sp("2px"); ctx.fillStyle=onDark?alpha(paper,.7):mute; if(tag.trim()) ctx.fillText(tag,P,T+190); sp("0px");
  let y; const bodyMax=tall?7:4;

  if(kind==="capa"){
    const f=fit(title,maxW,tall?7:6,tall?104:96,54,800,FT); ctx.fillStyle=fg; ctx.font=font(800,f.size,FT); sp("-1.5px"); y=block(f.ls,P,T+300+f.size*.4,f.size*1.04); sp("0px");
    if(body){ ctx.font=font(400,36,FB); ctx.fillStyle=fgMute; y=block(lines(body,maxW*.86).slice(0,bodyMax),P,y+34,50); }
    if(n>1&&!tall){ ctx.font=font(500,22,FL); sp("2px"); ctx.fillStyle=acc; ctx.fillText(lang==="en"?"SWIPE  →":"DESLIZE  →",P,FY-48); sp("0px"); } }
  else if(kind==="numero"){
    const st=tr(s.stat,lang); const f=fit(st,maxW,1,240,104,800,FT); ctx.fillStyle=acc; ctx.font=font(800,f.size,FT); sp("-6px"); ctx.fillText(st,P-6,T+250+f.size*.8); sp("0px");
    y=T+250+f.size*.8+90; const ft=fit(title,maxW,4,56,36,700,FT); ctx.fillStyle=ink; ctx.font=font(700,ft.size,FT); y=block(ft.ls,P,y,ft.size*1.15);
    if(body){ ctx.font=font(400,33,FB); ctx.fillStyle=alpha(ink,.7); block(lines(body,maxW).slice(0,5),P,y+26,46); }
    const src=tr(s.source,lang); if(src){ ctx.font=font(400,21,FL); ctx.fillStyle=mute; block(lines((lang==="en"?"Fonte / Source: ":"Fonte: ")+src,maxW).slice(0,2),P,FY-50,29); } }
  else if(kind==="frase"){
    const f=fit(title,maxW-48,tall?9:7,tall?80:72,42,700,FT); ctx.fillStyle=ink; ctx.font=font(700,f.size,FT); sp("-0.5px"); y=block(f.ls,P+48,T+250+f.size*.85,f.size*1.16); sp("0px");
    if(body){ ctx.font=font(400,32,FB); ctx.fillStyle=alpha(ink,.66); y=block(lines(body,maxW-48).slice(0,bodyMax),P+48,y+30,46); }
    ctx.fillStyle=acc; ctx.fillRect(P,T+250,8,y-T-250-f.size*.1); }
  else if(kind==="resumo"){
    // caixa "Em resumo" como nos artigos do site
    const items=String(body||"").split("\n").map(x=>x.replace(/^[-•·]\s*/,"").trim()).filter(Boolean).slice(0,tall?6:5);
    const ft=fit(title||(lang==="en"?"In short":"Em resumo"),maxW,3,64,40,800,FT); ctx.fillStyle=ink; ctx.font=font(800,ft.size,FT); sp("-1px"); y=block(ft.ls,P,T+260+ft.size*.4,ft.size*1.08); sp("0px");
    ctx.font=font(400,33,FB); const ls=items.map(t=>lines(t,maxW-120)); const bh=ls.reduce((a,l)=>a+l.length*46+26,0)+56;
    ctx.fillStyle=soft; rr(P,y+30,maxW,bh,14); ctx.fill(); let yy=y+30+64;
    ls.forEach((l,k)=>{ ctx.fillStyle=acc; ctx.font=font(500,22,FL); ctx.fillText(String(k+1).padStart(2,"0"),P+36,yy-4); ctx.fillStyle=ink; ctx.font=font(400,33,FB); yy=block(l,P+96,yy,46)+26; }); }
  else if(kind==="cta"){
    const f=fit(title,maxW,5,tall?92:84,48,800,FT); ctx.fillStyle=paper; ctx.font=font(800,f.size,FT); sp("-1.5px"); y=block(f.ls,P,T+300+f.size*.4,f.size*1.06); sp("0px");
    if(body){ ctx.font=font(400,36,FB); ctx.fillStyle=alpha(paper,.75); y=block(lines(body,maxW*.86).slice(0,5),P,y+36,50); }
    const bt=(tr(s.button,lang)||b.cta||"Diagnóstico Grátis")+"  →"; ctx.font=font(600,30,FB); const bw=ctx.measureText(bt).width+72;
    ctx.fillStyle=acc; rr(P,y+50,bw,84,42); ctx.fill(); ctx.fillStyle=b.accentInk||"#FFFFFF"; ctx.fillText(bt,P+36,y+50+53);
    ctx.font=font(500,22,FL); sp("1px"); ctx.fillStyle=alpha(paper,.6); ctx.fillText(site+"/pt",P+bw+28,y+50+52); sp("0px"); }
  else { // ponto
    ctx.fillStyle=acc; ctx.font=font(800,150,FT); sp("-6px"); ctx.fillText(String(pts).padStart(2,"0"),P-6,T+380); sp("0px");
    const f=fit(title,maxW,tall?6:4,tall?72:62,40,800,FT); ctx.fillStyle=ink; ctx.font=font(800,f.size,FT); sp("-1px"); y=block(f.ls,P,T+470+f.size*.3,f.size*1.1); sp("0px");
    if(body){ ctx.font=font(400,35,FB); ctx.fillStyle=alpha(ink,.72); block(lines(body,maxW).slice(0,tall?10:8),P,y+30,50); } }
}
