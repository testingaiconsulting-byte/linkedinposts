"""Gera os JPG (1080x1350) de um post da Atualiza Brasil 360 a partir dos slides da Central.
Uso: python3 atualiza360/_tools/render.py <post.json com {"slides":[...]}> <pasta de saida>
Slides: capa (fundo escuro), ponto (claro, numerado), cta (azul, com botao).
Paleta inspirada em cores de mapas; sem logotipos nem marcas de terceiros."""
import json, sys, base64, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, '..', '..', 'render', 'fonts') + '/'
def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()

BLUE, DARK, RED, YEL, GRN = '#1A73E8', '#202124', '#EA4335', '#FBBC04', '#34A853'
ACC = [BLUE, RED, YEL, GRN]

CSS = f"""@font-face{{font-family:A;src:url(data:font/ttf;base64,{b64(F+'Archivo.ttf')})}}
@font-face{{font-family:P;src:url(data:font/ttf;base64,{b64(F+'IBMPlexSans.ttf')})}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:P}}
.strip{{position:absolute;left:96px;top:96px;display:flex;gap:10px}}.strip i{{display:block;width:44px;height:10px;border-radius:5px}}
.eb{{position:absolute;left:96px;top:140px;font:600 25px P;letter-spacing:.14em;text-transform:uppercase}}
.c{{position:absolute;left:96px;right:96px}}
h1{{font:800 104px/1.04 A;letter-spacing:-.02em}} h2{{font:800 68px/1.1 A;letter-spacing:-.01em}}
.num{{font:900 150px/1 A}} p{{font:400 38px/1.55 P}}
.line{{position:absolute;left:96px;right:96px;top:1206px;height:2px}}
.brand{{position:absolute;left:96px;top:1236px;display:flex;align-items:center;gap:16px;font:800 32px A;letter-spacing:-.01em}}
.brand small{{font:600 22px P;letter-spacing:.1em;text-transform:uppercase;opacity:.7;margin-left:4px}}
.pg{{position:absolute;right:96px;top:1244px;font:400 25px P}}
.sw{{position:absolute;left:96px;top:1120px;font:600 30px P}}
.btn{{margin-top:64px;background:#fff;color:{BLUE};border-radius:60px;height:110px;display:flex;align-items:center;justify-content:center;font:600 36px P}}"""

TH = {'dark': dict(bg=DARK, fg='#fff', eb='#9AA0A6', body='#D7DADF', line='#3c4043', pg='#9AA0A6', brand='#fff'),
      'light': dict(bg='#FFFFFF', fg=DARK, eb='#5F6368', body='#4A4E53', line='#E3E5E8', pg='#80868B', brand=DARK),
      'blue': dict(bg=BLUE, fg='#fff', eb='#D2E3FC', body='#E8F0FE', line='#5B9BF0', pg='#D2E3FC', brand='#fff')}

def pin(color, hole):
    return (f'<svg width="30" height="42" viewBox="0 0 30 42"><path d="M15 0C6.7 0 0 6.7 0 15c0 11.2 15 27 15 27s15-15.8 15-27C30 6.7 23.3 0 15 0z" fill="{color}"/>'
            f'<circle cx="15" cy="15" r="6" fill="{hole}"/></svg>')

def esc(s): return (s or '').replace('&', '&amp;').replace('<', '&lt;')

def html(s, i, n):
    k = s['kind']; name = 'dark' if k == 'capa' else 'blue' if k == 'cta' else 'light'; t = TH[name]
    strip = '<div class="strip">' + ''.join(f'<i style="background:{"#fff" if name=="blue" else c}"></i>' for c in ACC) + '</div>'
    eb = f'<div class="eb" style="color:{t["eb"]}">{esc(s.get("eyebrow"))}</div>' if k == 'capa' and s.get('eyebrow') else ''
    if k == 'capa':
        body = f'<div class="c" style="top:260px"><h1 style="color:{t["fg"]}">{esc(s["title"])}</h1><p style="color:{t["body"]};margin-top:70px">{esc(s.get("body"))}</p></div>'
    elif k == 'ponto':
        col = ACC[(i - 1) % 4] if ACC[(i - 1) % 4] != YEL else '#E8A600'
        body = f'<div class="c" style="top:240px"><div class="num" style="color:{col}">{i:02d}</div><h2 style="color:{t["fg"]};margin-top:40px">{esc(s["title"])}</h2><p style="color:{t["body"]};margin-top:50px">{esc(s.get("body"))}</p></div>'
    else:
        btn = f'<div class="btn">{esc(s.get("button"))}</div>' if s.get('button') else ''
        body = f'<div class="c" style="top:290px"><h1 style="color:{t["fg"]};font-size:94px">{esc(s["title"])}</h1><p style="color:{t["body"]};margin-top:60px">{esc(s.get("body"))}</p>{btn}</div>'
    sw = f'<div class="sw" style="color:{"#8AB4F8" if name=="dark" else BLUE}">Arraste →</div>' if i == 0 and n > 1 else ''
    hole = t['bg']
    brand = f'<div class="brand" style="color:{t["brand"]}">{pin("#fff" if name=="blue" else RED, hole)}Atualiza Brasil <span style="color:{"#fff" if name=="blue" else BLUE}">360</span></div>'
    return (f'<html><head><meta charset=utf-8><style>{CSS}</style></head><body style="background:{t["bg"]}">{strip}{eb}{body}{sw}'
            f'<div class="line" style="background:{t["line"]}"></div>{brand}<div class="pg" style="color:{t["pg"]}">{i+1}/{n}</div></body></html>')

post = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
sl = post['slides']
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1350})
    for i, s in enumerate(sl):
        pg.set_content(html(s, i, len(sl))); pg.wait_for_timeout(150)
        pg.screenshot(path=f'{out}/{i+1:02d}.jpg', type='jpeg', quality=92)
    b.close()
print(sorted(os.listdir(out)))
