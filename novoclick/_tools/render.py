"""Gera os JPG (1080x1350) de um post do Novoclick a partir dos slides da Central.
Uso: python3 novoclick/_tools/render.py <post.json com {"slides":[...]}> <pasta de saida>
Slides: capa ou prazo (fundo escuro), ponto (claro, numerado), cta (verde, com botao)."""
import json,sys,base64,os
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
F=os.path.join(HERE,'..','..','render','fonts')+'/'
def b64(p): return base64.b64encode(open(p,'rb').read()).decode()
CSS=f"""@font-face{{font-family:A;src:url(data:font/ttf;base64,{b64(F+'Archivo.ttf')})}}
@font-face{{font-family:P;src:url(data:font/ttf;base64,{b64(F+'IBMPlexSans.ttf')})}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:P}}
.bar{{position:absolute;left:96px;top:96px;width:72px;height:9px}}
.eb{{position:absolute;left:96px;top:140px;font:600 25px P;letter-spacing:.14em;text-transform:uppercase}}
.c{{position:absolute;left:96px;right:96px}}
h1{{font:800 108px/1.03 A;letter-spacing:-.02em}} h2{{font:800 66px/1.12 A;letter-spacing:-.01em}}
.num{{font:900 150px/1 A}} p{{font:400 37px/1.58 P}}
.line{{position:absolute;left:96px;right:96px;top:1206px;height:2px}}
.logo{{position:absolute;left:90px;top:1208px}}
.pg{{position:absolute;right:96px;top:1232px;font:400 25px P}}
.sw{{position:absolute;left:96px;top:1120px;font:600 30px P}}
.btn{{margin-top:60px;background:#fff;color:#2E9E4A;border-radius:60px;height:110px;display:flex;align-items:center;justify-content:center;font:600 34px P}}"""
TH={'dark':dict(bg='#2B2E33',fg='#fff',bar='#7DD49F',eb='#AFB0B4',body='#D2D3D5',line='#5a5d62',pg='#9a9ca0'),
    'light':dict(bg='#F3F5F2',fg='#2E3235',bar='#2E9E4A',eb='#8a8d90',body='#55595c',line='#cfd2cf',pg='#8a8d90'),
    'green':dict(bg='#2E9E4A',fg='#fff',bar='#fff',eb='#d8f0df',body='#eef8f1',line='#7cc792',pg='#d8f0df')}
def esc(s): return (s or '').replace('&','&amp;').replace('<','&lt;')
def html(s,i,n):
    k=s['kind']; t=TH['dark' if k in('capa','prazo') else 'green' if k=='cta' else 'light']
    logo=b64(os.path.join(HERE,f"logo_{'dark' if k in('capa','prazo') else 'green' if k=='cta' else 'light'}.png"))
    eb=f'<div class="eb" style="color:{t["eb"]}">{esc(s.get("eyebrow"))}</div>' if k in('capa','prazo') else ''
    if k=='prazo': body=f'<div class="c" style="top:250px"><div class="num" style="color:#7DD49F;font-size:170px">{esc(s.get("stat"))}</div><h2 style="color:{t["fg"]};margin-top:50px;font-size:76px">{esc(s["title"])}</h2><p style="color:{t["body"]};margin-top:50px">{esc(s.get("body"))}</p></div>'
    elif k=='capa': body=f'<div class="c" style="top:270px"><h1 style="color:{t["fg"]}">{esc(s["title"])}</h1><p style="color:{t["body"]};margin-top:70px">{esc(s.get("body"))}</p></div>'
    elif k=='ponto': body=f'<div class="c" style="top:240px"><div class="num" style="color:#2E9E4A">{i:02d}</div><h2 style="color:{t["fg"]};margin-top:40px">{esc(s["title"])}</h2><p style="color:{t["body"]};margin-top:50px">{esc(s.get("body"))}</p></div>'
    else: body=f'<div class="c" style="top:300px"><h1 style="color:{t["fg"]};font-size:96px">{esc(s["title"])}</h1><p style="color:{t["body"]};margin-top:60px">{esc(s.get("body"))}</p>'+(f'<div class="btn">{esc(s.get("button") or "Envie-nos mensagem")}</div>' if s.get('button',True) is not None else '')+'</div>'
    sw=f'<div class="sw" style="color:{t["bar"]}">Deslize →</div>' if i==0 and n>1 else ''
    return f'<html><head><meta charset=utf-8><style>{CSS}</style></head><body style="background:{t["bg"]}"><div class="bar" style="background:{t["bar"]}"></div>{eb}{body}{sw}<div class="line" style="background:{t["line"]}"></div><img class="logo" src="data:image/png;base64,{logo}"><div class="pg" style="color:{t["pg"]}">{i+1}/{n}</div></body></html>'
post=json.load(open(sys.argv[1])); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
sl=post['slides']
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1350})
    for i,s in enumerate(sl):
        if s['kind']=='cta': s.setdefault('button','Envie-nos mensagem')
        pg.set_content(html(s,i,len(sl))); pg.wait_for_timeout(150)
        pg.screenshot(path=f'{out}/{i+1:02d}.jpg',type='jpeg',quality=92)
    b.close()
print(sorted(os.listdir(out)))
