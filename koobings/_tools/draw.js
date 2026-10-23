// Koobings Instagram visuals. drawSlide(canvas, slides, index, opts)
const BRAND={name:"Koobings",primary:"#0044FF",primaryDark:"#0036CC",accent:"#FFCB1A",soft:"#EEF3FF",paper:"#FFFFFF",ink:"#111111",FT:"Inter",FB:"Inter"};
function font(w,size,fam){ return `${w} ${size}px "${fam}", sans-serif`; }
function lines(ctx,text,maxW){ const out=[]; String(text||"").split("\n").forEach(par=>{ const words=par.split(/[ \t]+/).filter(Boolean); if(!words.length){out.push("");return;} let line=words[0]; for(let i=1;i<words.length;i++){ const t=line+" "+words[i]; if(ctx.measureText(t).width<=maxW) line=t; else {out.push(line); line=words[i];} } out.push(line); }); return out; }
function fit(ctx,text,maxW,maxLines,start,min,w,fam){ let size=start,ls; for(;size>=min;size-=4){ ctx.font=font(w,size,fam); ls=lines(ctx,text,maxW); if(ls.length<=maxLines) break; } return {size:Math.max(size,min),ls}; }
function block(ctx,ls,x,y,lh){ ls.forEach((l,i)=>ctx.fillText(l,x,y+i*lh)); return y+ls.length*lh; }
function alpha(hex,a){ const n=parseInt(hex.replace("#",""),16); return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`; }
function spacing(ctx,v){ try{ ctx.letterSpacing=v; }catch(e){} }
function logo(ctx,x,y,col,size,dark){
  const q=size*1.25, top=y-size*0.95; ctx.fillStyle=dark?"#FFFFFF":BRAND.primary; roundRect(ctx,x,top,q,q,q*0.24); ctx.fill();
  ctx.fillStyle=dark?BRAND.primary:"#FFFFFF"; ctx.font=font(800,size*0.86,BRAND.FB); const kw=ctx.measureText("K").width; ctx.fillText("K",x+(q-kw)/2,top+q*0.74);
  ctx.fillStyle=col; ctx.font=font(700,size,BRAND.FB); spacing(ctx,"-0.5px"); ctx.fillText("Koobings",x+q+size*0.4,y); spacing(ctx,"0px");
}
function drawSlide(cv,slides,i,opts){
  opts=opts||{}; const W=cv.width,H=cv.height,P=96, ctx=cv.getContext("2d"), B=BRAND;
  const reel=H>1500, n=slides.length, s=slides[i], kind=s.kind||"ponto", dark=(kind==="capa"||kind==="cta");
  const bg=dark?B.primary:B.paper, fg=dark?B.paper:B.ink, ac=dark?B.accent:B.primary, maxW=W-2*P-(reel?60:0), K=reel?1.3:1;
  const top=reel?330:0, show=opts.show==null?2:opts.show; // show: 1 = title only, 2 = all
  ctx.textBaseline="alphabetic"; if(dark){ const g=ctx.createLinearGradient(0,0,W,H); g.addColorStop(0,"#1F5BFF"); g.addColorStop(1,B.primaryDark); ctx.fillStyle=g; } else ctx.fillStyle=bg; ctx.fillRect(0,0,W,H);
  // decorative blob
  ctx.fillStyle=dark?"rgba(255,255,255,.08)":B.soft; ctx.beginPath(); ctx.arc(W-40,top+150,230,0,Math.PI*2); ctx.fill();
  ctx.fillStyle=ac; ctx.fillRect(P,top+P,64,10);
  const eb=s.eyebrow||"";
  if(eb){ ctx.fillStyle=alpha(fg,dark?.75:.6); ctx.font=font(600,26,B.FB); spacing(ctx,"3px"); ctx.fillText(eb.toUpperCase().slice(0,44),P,top+P+64); spacing(ctx,"0px"); }
  const title=s.title||"", body=show>1?(s.body||""):""; let y; const o=top;
  if(kind==="capa"){ const f=fit(ctx,title,maxW,6,108*K,60,800,B.FT); ctx.fillStyle=fg; ctx.font=font(800,f.size,B.FT); y=block(ctx,f.ls,P,o+340,f.size*1.08);
    if(body){ ctx.font=font(400,40*K,B.FB); ctx.fillStyle=alpha(fg,.82); block(ctx,lines(ctx,body,maxW).slice(0,5),P,y+40,54*K); }
    if(n>1&&!reel){ ctx.fillStyle=ac; ctx.font=font(600,30,B.FB); ctx.fillText("Deslize →",P,H-190); } }
  else if(kind==="numero"){ const st=s.stat||""; const f=fit(ctx,st,maxW,1,300,120,800,B.FT); ctx.fillStyle=ac; ctx.font=font(800,f.size,B.FT); ctx.fillText(st,P-6,o+300+f.size*.82);
    y=o+300+f.size*.82+f.size*.22+70; const ft=fit(ctx,title,maxW,4,64,40,700,B.FT); ctx.fillStyle=fg; ctx.font=font(700,ft.size,B.FT); y=block(ctx,ft.ls,P,y,ft.size*1.15);
    if(body){ ctx.font=font(400,38,B.FB); ctx.fillStyle=alpha(fg,.78); block(ctx,lines(ctx,body,maxW).slice(0,6),P,y+30,52); } }
  else if(kind==="frase"){ if(!reel&&!s.noquote&&!/^[“"]/.test(title)){ ctx.fillStyle=ac; ctx.font=font(800,220,"DejaVu Serif"); ctx.fillText("“",P-10,o+430); } const f=fit(ctx,title,maxW,7,reel?130:80,46,750,B.FT); ctx.fillStyle=fg; ctx.font=font(750,f.size,B.FT); y=block(ctx,f.ls,P,o+500,f.size*1.14);
    if(body){ ctx.font=font(400,reel?54:38,B.FB); ctx.fillStyle=alpha(fg,.72); block(ctx,lines(ctx,body,maxW).slice(0,4),P,y+44,reel?72:52); } }
  else if(kind==="cta"){ const f=fit(ctx,title,maxW,5,92*K,52,800,B.FT); ctx.fillStyle=fg; ctx.font=font(800,f.size,B.FT); y=block(ctx,f.ls,P,o+380,f.size*1.1);
    if(body){ ctx.font=font(400,42*K,B.FB); ctx.fillStyle=alpha(fg,.85); y=block(ctx,lines(ctx,body,maxW).slice(0,6),P,y+44,58*K); }
    // button
    const bw=520,bh=104,by=y+70; ctx.fillStyle=B.accent; roundRect(ctx,P,by,bw,bh,52); ctx.fill(); ctx.fillStyle=B.ink; ctx.font=font(700,38,B.FB); ctx.fillText("Experimentar grátis →",P+56,by+66); }
  else { const idx=slides.slice(0,i+1).filter(x=>(x.kind||"ponto")==="ponto").length; ctx.fillStyle=ac; ctx.font=font(800,150,B.FT); ctx.fillText(String(idx).padStart(2,"0"),P-6,o+350);
    const f=fit(ctx,title,maxW,5,72*K,44,750,B.FT); ctx.fillStyle=fg; ctx.font=font(750,f.size,B.FT); y=block(ctx,f.ls,P,o+470,f.size*1.12);
    if(body){ ctx.font=font(400,reel?52:40,B.FB); ctx.fillStyle=alpha(fg,.78); block(ctx,lines(ctx,body,maxW).slice(0,9),P,y+44,reel?70:56); } }
  const fy=reel?H-330:H-80;
  ctx.fillStyle=alpha(fg,.18); ctx.fillRect(P,fy-50,maxW,2);
  logo(ctx,P,fy,fg,34,dark);
  if(n>1&&!reel){ ctx.font=font(500,26,B.FB); ctx.fillStyle=alpha(fg,.55); const t=`${i+1}/${n}`; ctx.fillText(t,W-P-ctx.measureText(t).width,fy); }
}function roundRect(ctx,x,y,w,h,r){ ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); }
