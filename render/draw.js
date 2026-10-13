// Visual "Claudio Braga · AI Consulting": branco, preto e cinzento, com a arte em linhas e o logo CB.
// drawSlideCB(canvas, post, indiceDoSlide, lingua, marca, imagens{art,logo}, opcoes{layer,drift})
// Formatos: 1080x1350 (feed) e 1080x1920 (reel/story, com margens para a interface do Instagram).
// opcoes.layer: "bg" (fundo, arte e rodapé), "text" (só o texto) ou nada (tudo). opcoes.drift: segundos (move a arte).
function drawSlideCB(cv,p,i,lang,b,imgs,opts){
  imgs=imgs||{}; opts=opts||{};
  const W=cv.width,H=cv.height,P=96,maxW=W-2*P;
  const tall=H>1700, T=tall?250:0, FY=tall?H-430:H-150;
  const ctx=cv.getContext("2d");
  const ink=b.ink||"#111111", paper=b.paper||"#FFFFFF", mute=b.muted||"#8A8A8A";
  const FT=b.fontTitle||"Space Grotesk", FB=b.fontBody||"Space Grotesk", FL=b.fontLabel||"Syncopate";
  const tr=(v,l)=>v==null?"":(typeof v==="string"?v:(v[l]??v.pt??v.en??""));
  const font=(w,s,f)=>w+" "+s+'px "'+f+'", sans-serif';
  const lines=(text,mw)=>{ const out=[]; String(text||"").split("\n").forEach(par=>{ const ws=par.split(/[ \t]+/).filter(Boolean); if(!ws.length){out.push("");return;} let ln=ws[0]; for(let k=1;k<ws.length;k++){ const t=ln+" "+ws[k]; if(ctx.measureText(t).width<=mw) ln=t; else {out.push(ln); ln=ws[k];} } out.push(ln); }); return out; };
  const fit=(text,mw,maxL,start,min,w,f)=>{ let s=start,ls; for(;s>=min;s-=4){ ctx.font=font(w,s,f); ls=lines(text,mw); if(ls.length<=maxL) break; } return {size:Math.max(s,min),ls}; };
  const block=(ls,x,y,lh)=>{ ls.forEach((l,k)=>ctx.fillText(l,x,y+k*lh)); return y+ls.length*lh; };
  const sp=v=>{ try{ ctx.letterSpacing=v; }catch(e){} };
  const alpha=(hex,a)=>{ const h=String(hex).replace("#",""); const n=parseInt(h.length===3?h.split("").map(c=>c+c).join(""):h,16)||0; return "rgba("+(n>>16&255)+","+(n>>8&255)+","+(n&255)+","+a+")"; };
  const first=t=>String(t||"").split("\n").find(l=>l.trim())||"";
  const slides=(p.slides&&p.slides.length)?p.slides:[{kind:"frase",title:first(tr(p.texts,lang))}];
  const n=slides.length, s=slides[Math.min(i,n-1)], kind=s.kind||"ponto";
  const title=tr(s.title,lang), body=tr(s.body,lang);
  const big=kind==="capa"||kind==="cta";
  ctx.textBaseline="alphabetic";
  if(opts.layer!=="text"){
    ctx.fillStyle=paper; ctx.fillRect(0,0,W,H);
    if(imgs.art&&imgs.art.width){ const a=imgs.art, r=a.height/a.width, d=opts.drift||0;
      const soft=(w,h)=>{ const o=document.createElement("canvas"); o.width=Math.round(w); o.height=Math.round(h); const c=o.getContext("2d"); c.drawImage(a,0,0,o.width,o.height);
        c.globalCompositeOperation="destination-in"; c.save(); c.translate(o.width/2,o.height/2); c.scale(o.width/2,o.height/2);
        const g=c.createRadialGradient(0,0,0,0,0,1); g.addColorStop(0,"rgba(0,0,0,1)"); g.addColorStop(.62,"rgba(0,0,0,.9)"); g.addColorStop(1,"rgba(0,0,0,0)");
        c.fillStyle=g; c.beginPath(); c.arc(0,0,1,0,Math.PI*2); c.fill(); c.restore(); return o; };
      const dx=Math.sin(d*0.35)*40, dy=Math.cos(d*0.27)*24, sc=1+0.04*Math.sin(d*0.2);
      if(big||tall){ const w=W*(tall?1.6:1.25)*sc, h=w*r; ctx.globalAlpha=tall&&!big?.22:.6; ctx.drawImage(soft(w,h),W-w*.86+dx,(tall?FY-h+80:H-h-90)+dy); }
      else { const w=W*.7*sc, h=w*r; ctx.globalAlpha=.18; ctx.drawImage(soft(w,h),W-w*.7+dx,-h*.22+dy); }
      ctx.globalAlpha=1; }
    // rodapé: logo + assinatura + número do slide
    ctx.fillStyle=paper; ctx.globalAlpha=.9; ctx.fillRect(0,FY,W,tall?140:150); ctx.globalAlpha=1;
    ctx.fillStyle=alpha(ink,.85); ctx.fillRect(P,FY,maxW,1.5);
    let x=P; if(imgs.logo&&imgs.logo.width){ ctx.drawImage(imgs.logo,P-6,FY+22,76,76); x=P+84; }
    ctx.fillStyle=ink; ctx.font=font(700,17,FL); sp("4px"); ctx.fillText((b.name||"CLAUDIO BRAGA").toUpperCase(),x,FY+58);
    ctx.fillStyle=mute; ctx.fillText((b.tagline||"AI CONSULTING").toUpperCase(),x,FY+86); sp("0px");
    if(n>1&&!tall){ ctx.font=font(500,24,FB); ctx.fillStyle=mute; const t=(Math.min(i,n-1)+1)+" / "+n; ctx.fillText(t,W-P-ctx.measureText(t).width,FY+76); }
  }
  if(opts.layer==="bg") return;
  // etiqueta
  const eb=tr(s.eyebrow,lang)||p.pilar||"";
  ctx.fillStyle=ink; ctx.fillRect(P,T+P,48,3);
  ctx.fillStyle=alpha(ink,.62); ctx.font=font(700,19,FL); sp("5px"); ctx.fillText(eb.toUpperCase().slice(0,40),P,T+P+50); sp("0px");
  let y; const bodyMax=tall?7:4;
  if(kind==="capa"){ const f=fit(title,maxW,tall?7:6,tall?108:100,56,700,FT); ctx.fillStyle=ink; ctx.font=font(700,f.size,FT); sp("-1px"); y=block(f.ls,P,T+300,f.size*1.06); sp("0px");
    if(body){ ctx.font=font(400,38,FB); ctx.fillStyle=alpha(ink,.72); y=block(lines(body,maxW*.9).slice(0,bodyMax),P,y+36,52); }
    if(n>1&&!tall){ ctx.fillStyle=ink; ctx.font=font(700,18,FL); sp("4px"); ctx.fillText(lang==="en"?"SWIPE →":"DESLIZE →",P,H-200); sp("0px"); } }
  else if(kind==="numero"){ const st=tr(s.stat,lang); const f=fit(st,maxW,1,250,110,700,FT); ctx.fillStyle=ink; ctx.font=font(700,f.size,FT); sp("-4px"); ctx.fillText(st,P-8,T+260+f.size*.8); sp("0px");
    y=T+260+f.size*.8+100; const ft=fit(title,maxW,4,58,38,600,FT); ctx.fillStyle=ink; ctx.font=font(600,ft.size,FT); y=block(ft.ls,P,y,ft.size*1.16);
    if(body){ ctx.font=font(400,34,FB); ctx.fillStyle=alpha(ink,.7); block(lines(body,maxW).slice(0,6),P,y+28,48); }
    const src=tr(s.source,lang); if(src){ ctx.font=font(400,23,FB); ctx.fillStyle=mute; block(lines((lang==="en"?"Source: ":"Fonte: ")+src,maxW).slice(0,2),P,FY-55,31); } }
  else if(kind==="frase"){ ctx.fillStyle=alpha(ink,.18); ctx.font=font(700,260,FT); ctx.fillText("“",P-14,T+440); const f=fit(title,maxW,tall?9:7,tall?84:76,44,600,FT); ctx.fillStyle=ink; ctx.font=font(600,f.size,FT); y=block(f.ls,P,T+470,f.size*1.18);
    if(body){ ctx.font=font(400,34,FB); ctx.fillStyle=alpha(ink,.66); block(lines(body,maxW).slice(0,bodyMax),P,y+36,48); } }
  else if(kind==="cta"){ const f=fit(title,maxW,5,tall?92:84,50,700,FT); ctx.fillStyle=ink; ctx.font=font(700,f.size,FT); sp("-1px"); y=block(f.ls,P,T+320,f.size*1.08); sp("0px");
    if(body){ ctx.font=font(400,38,FB); ctx.fillStyle=alpha(ink,.72); y=block(lines(body,maxW*.9).slice(0,5),P,y+40,52); } ctx.fillStyle=ink; ctx.fillRect(P,y+44,96,3); }
  else { const idx=slides.slice(0,i+1).filter(x=>(x.kind||"ponto")==="ponto").length; ctx.fillStyle=alpha(ink,.22); ctx.font=font(700,120,FL); ctx.fillText(String(idx).padStart(2,"0"),P-6,T+320);
    const f=fit(title,maxW,tall?6:4,tall?76:64,42,700,FT); ctx.fillStyle=ink; ctx.font=font(700,f.size,FT); sp("-0.5px"); y=block(f.ls,P,T+440,f.size*1.12); sp("0px");
    if(body){ ctx.font=font(400,36,FB); ctx.fillStyle=alpha(ink,.72); block(lines(body,maxW).slice(0,tall?10:9),P,y+34,52); } }
}
