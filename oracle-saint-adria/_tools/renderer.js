/* ============ canvas renderer ============ */
const THEMES={classic:{bg:"#0F2F1A",ink:"#BF8448",soft:"#E6C79C",frame:false},midnight:{bg:"#0A100C",ink:"#C99556",soft:"#E6C79C",frame:true},gold:{bg:"#BF8448",ink:"#0F2F1A",soft:"#163D24",frame:true}};
const FF="Montserrat, 'Arial Black', sans-serif";
const img=new Image(); let imgReady=new Promise(r=>{img.onload=r;img.onerror=r;}); img.src=MASCOT;
const fontsReady=Promise.all([document.fonts.load(`800 80px Montserrat`),document.fonts.load(`700 40px Montserrat`),document.fonts.load(`600 40px Montserrat`)]).catch(()=>{});
const ready=Promise.all([imgReady,fontsReady]);
let HANDLE="FOLLOW @ORACLE_SAINT_ADRIA";

function font(ctx,w,s){ctx.font=`${w} ${s}px ${FF}`;}
function fit(ctx,text,w,size,maxW,min){min=min||22;font(ctx,w,size);while(ctx.measureText(text).width>maxW&&size>min){size-=2;font(ctx,w,size);}return size;}
function wrap(ctx,text,maxW){const out=[];String(text||"").split("\n").forEach(par=>{const words=par.split(/\s+/).filter(Boolean);let line="";words.forEach(wd=>{const t=line?line+" "+wd:wd;if(ctx.measureText(t).width>maxW&&line){out.push(line);line=wd;}else line=t;});if(line)out.push(line);});return out;}
function drawMascot(ctx,th,cx,cy,scale){const w=600*scale,h=480*scale;if(!img.naturalWidth)return;
  if(!th.frame){ctx.drawImage(img,cx-w/2,cy-h/2,w,h);return;}
  const r=h*.6;ctx.save();ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.fillStyle="#0F2F1A";ctx.fill();ctx.clip();ctx.drawImage(img,cx-w/2,cy-h/2+h*.04,w,h);ctx.restore();
  ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.lineWidth=6*scale+2;ctx.strokeStyle=th.ink;ctx.stroke();}
function mark(ctx,m,x,y,r,col){if(!m)return;ctx.save();ctx.strokeStyle=col;ctx.fillStyle=col;ctx.lineWidth=r*.2;ctx.lineCap="round";ctx.lineJoin="round";
  ctx.beginPath();ctx.arc(x,y,r-ctx.lineWidth/2,0,Math.PI*2);ctx.stroke();ctx.beginPath();
  if(m==="+"){ctx.moveTo(x-r*.42,y+r*.02);ctx.lineTo(x-r*.12,y+r*.32);ctx.lineTo(x+r*.44,y-r*.3);ctx.stroke();}
  else if(m==="x"){const d=r*.32;ctx.moveTo(x-d,y-d);ctx.lineTo(x+d,y+d);ctx.moveTo(x+d,y-d);ctx.lineTo(x-d,y+d);ctx.stroke();}
  else{font(ctx,800,r*1.1);ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText("?",x,y+r*.05);}
  ctx.restore();}
function footer(ctx,th){ctx.fillStyle=th.ink;ctx.textAlign="center";ctx.textBaseline="middle";fit(ctx,HANDLE,800,50,960);ctx.fillText(HANDLE,540,1262);
  ctx.globalAlpha=.7;font(ctx,600,22);ctx.fillText("18+ · GAMBLE RESPONSIBLY",540,1318);ctx.globalAlpha=1;}
function kicker(ctx,th,text,y,boxed){if(!text)return;font(ctx,700,32);ctx.textAlign="center";ctx.textBaseline="middle";const t=text.toUpperCase();
  if(boxed){const w=Math.min(ctx.measureText(t).width+64,980);ctx.strokeStyle=th.ink;ctx.lineWidth=4;roundRect(ctx,540-w/2,y-34,w,68,34);ctx.stroke();}
  ctx.fillStyle=boxed?th.ink:th.soft;fit(ctx,t,700,32,boxed?916:960);ctx.fillText(t,540,y+1);}
function roundRect(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function textBlock(ctx,text,w,size,maxW,maxLines,yTop,col,lh){let lines;do{font(ctx,w,size);lines=wrap(ctx,text,maxW);if(lines.length<=maxLines&&lines.every(l=>ctx.measureText(l).width<=maxW))break;size-=2;}while(size>24);
  ctx.fillStyle=col;ctx.textAlign="center";ctx.textBaseline="top";const step=size*(lh||1.12);lines.forEach((l,i)=>ctx.fillText(l,540,yTop+i*step));return yTop+lines.length*step;}

function render(ctx,slide,themeId){const th=THEMES[themeId]||THEMES.classic;const s=slide||{};
  ctx.fillStyle=th.bg;ctx.fillRect(0,0,1080,1350);
  if(s.tpl==="score"){
    kicker(ctx,th,s.kicker||"UPSET ALERT",120,true);
    const rows=[[s.teamA,s.scoreA],[s.teamB,s.scoreB]];
    rows.forEach((r,i)=>{const y=i?520:330;ctx.fillStyle=th.ink;ctx.textBaseline="middle";
      ctx.textAlign="right";font(ctx,800,170);ctx.fillText(String(r[1]||""),1000,y+6);
      ctx.textAlign="left";fit(ctx,String(r[0]||"").toUpperCase(),800,86,700,36);ctx.fillText(String(r[0]||"").toUpperCase(),80,y);});
    ctx.globalAlpha=.35;ctx.fillStyle=th.ink;ctx.fillRect(80,424,920,4);ctx.globalAlpha=1;
    let y=textBlock(ctx,s.head||"",800,60,920,3,660,th.ink);
    if(s.sub)textBlock(ctx,s.sub,600,38,900,2,y+18,th.soft,1.25);
    drawMascot(ctx,th,540,1075,.38);
  } else if(s.tpl==="statement"){
    drawMascot(ctx,th,540,330,.6);
    kicker(ctx,th,s.kicker,92,false);
    let y=textBlock(ctx,s.head||"",800,84,940,5,560,th.ink,1.1);
    if(s.sub)textBlock(ctx,s.sub,600,42,900,3,y+30,th.soft,1.28);
  } else {
    const title=s.title||"";ctx.fillStyle=th.ink;ctx.textAlign="center";ctx.textBaseline="middle";fit(ctx,title,800,96,960);ctx.fillText(title,540,128);
    drawMascot(ctx,th,540,440,1);
    const L=(s.lines||[]).slice(0,4),n=L.length||1,step=n>3?112:130,y0=n>3?760:775;
    L.forEach((l,i)=>{const y=y0+i*step,r=n>3?42:46;mark(ctx,l.mark,147,y,r,th.ink);
      let noteW=0;if(l.note){font(ctx,700,46);noteW=ctx.measureText(l.note).width;ctx.fillStyle=th.soft;ctx.textAlign="right";ctx.textBaseline="middle";ctx.fillText(l.note,1020,y+2);}
      const x=l.mark?235:90,t=l.t||"";ctx.fillStyle=th.ink;ctx.textAlign="left";ctx.textBaseline="middle";fit(ctx,t,800,n>3?68:78,1020-x-(noteW?noteW+28:0),30);ctx.fillText(t,x,y+3);});
  }
  footer(ctx,th);}

