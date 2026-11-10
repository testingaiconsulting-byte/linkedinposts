"""Gera os JPG (1080x1350) de um post da Atualiza Brasil 360 a partir dos slides da Central.
Uso: python3 atualiza360/_tools/render.py <post.json com {"slides":[...]}> <pasta de saida>
Slides: capa, ponto (numerado), cta (azul, com botao). Campo opcional \"foto\": caminho de uma fotografia (relativo ao json) usada como fundo, com degrade escuro e texto branco.
Estilo Google/Material (Roboto, branco, azul #1A73E8 e as 4 cores); sem logotipos nem marcas da Google."""
import json, sys, base64, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, '..', '..', 'render', 'fonts') + '/'
def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()

BLUE, DARK, RED, YEL, GRN, GREY = '#1A73E8', '#202124', '#EA4335', '#FBBC04', '#34A853', '#5F6368'
ACC = [BLUE, RED, YEL, GRN]
R = os.path.join(HERE, 'Roboto.ttf')

CSS = f"""@font-face{{font-family:R;src:url(data:font/ttf;base64,{b64(R)});font-weight:100 900}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:R}}
.strip{{position:absolute;left:0;right:0;top:0;height:14px;display:flex}}.strip i{{flex:1}}
.eb{{position:absolute;left:96px;top:120px;display:flex;align-items:center;gap:14px;font:500 27px R;letter-spacing:.02em}}
.chip{{border:2px solid #DADCE0;border-radius:40px;padding:10px 26px 10px 18px;display:flex;align-items:center;gap:12px}}
.c{{position:absolute;left:96px;right:96px}}
h1{{font:700 100px/1.08 R;letter-spacing:-.02em}} h2{{font:700 66px/1.14 R;letter-spacing:-.01em}}
p{{font:400 38px/1.55 R}}
.dot{{width:120px;height:120px;border-radius:60px;display:flex;align-items:center;justify-content:center;font:700 54px R;color:#fff}}
.line{{position:absolute;left:96px;right:96px;top:1206px;height:2px}}
.brand{{position:absolute;left:96px;top:1236px;display:flex;align-items:center;gap:16px;font:700 32px R;letter-spacing:-.01em}}
.pg{{position:absolute;right:96px;top:1244px;font:400 25px R}}
.sw{{position:absolute;left:96px;top:1120px;font:500 30px R}}
.dots{{display:flex;gap:14px;margin-top:64px}}.dots i{{width:22px;height:22px;border-radius:11px;display:block}}
.btn{{margin-top:64px;background:#fff;color:{BLUE};border-radius:60px;height:112px;display:flex;align-items:center;justify-content:center;font:500 38px R;box-shadow:0 2px 6px rgba(0,0,0,.18)}}"""

TH = {'capa': dict(bg='#FFFFFF', fg=DARK, eb=GREY, body=GREY, line='#E8EAED', pg='#80868B', brand=DARK),
      'ponto': dict(bg='#F8F9FA', fg=DARK, eb=GREY, body='#3C4043', line='#E0E3E7', pg='#80868B', brand=DARK),
      'cta': dict(bg=BLUE, fg='#fff', eb='#D2E3FC', body='#E8F0FE', line='#5B9BF0', pg='#D2E3FC', brand='#fff')}

def pin(color, hole, w=30):
    h = int(w * 1.4)
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 30 42"><path d="M15 0C6.7 0 0 6.7 0 15c0 11.2 15 27 15 27s15-15.8 15-27C30 6.7 23.3 0 15 0z" fill="{color}"/>'
            f'<circle cx="15" cy="15" r="6" fill="{hole}"/></svg>')

def foto_css(s):
    f = s.get('foto')
    if not f: return ''
    if not os.path.isabs(f): f = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), f)
    mime = 'png' if f.lower().endswith('.png') else 'jpeg'
    return (f"linear-gradient(180deg,rgba(32,33,36,.15) 0%,rgba(32,33,36,.55) 45%,rgba(32,33,36,.92) 100%),"
            f"url(data:image/{mime};base64,{b64(f)}) center/cover no-repeat")

def esc(s): return (s or '').replace('&', '&amp;').replace('<', '&lt;')

def html(s, i, n):
    k = s['kind'] if s['kind'] in TH else 'ponto'; t = dict(TH[k])
    fc = foto_css(s)
    if fc: t.update(fg='#fff', body='#E8EAED', eb='#E8EAED', line='rgba(255,255,255,.35)', pg='#E8EAED', brand='#fff', bg=fc)
    strip = '<div class="strip">' + ''.join(f'<i style="background:{c}"></i>' for c in ACC) + '</div>' if k != 'cta' else ''
    eb = (f'<div class="eb" style="color:{t["eb"]}"><span class="chip">{pin(RED, "#fff", 22)}{esc(s.get("eyebrow"))}</span></div>'
          if k == 'capa' and s.get('eyebrow') else '')
    if k == 'capa':
        dots = '<div class="dots">' + ''.join(f'<i style="background:{c}"></i>' for c in ACC) + '</div>'
        top = "top:460px" if fc else 'top:280px'
        body = f'<div class="c" style="{top}"><h1 style="color:{t["fg"]}">{esc(s["title"])}</h1>{dots}<p style="color:{t["body"]};margin-top:56px">{esc(s.get("body"))}</p></div>'
    elif k == 'ponto':
        col = ACC[(i - 1) % 4]
        body = f'<div class="c" style="top:{"620px" if fc else "220px"}"><div class="dot" style="background:{col}">{i}</div><h2 style="color:{t["fg"]};margin-top:56px">{esc(s["title"])}</h2><p style="color:{t["body"]};margin-top:44px">{esc(s.get("body"))}</p></div>'
    else:
        btn = f'<div class="btn">{esc(s.get("button"))}</div>' if s.get('button') else ''
        body = f'<div class="c" style="top:280px">{pin("#fff", BLUE, 56)}<h1 style="color:{t["fg"]};font-size:92px;margin-top:40px">{esc(s["title"])}</h1><p style="color:{t["body"]};margin-top:52px">{esc(s.get("body"))}</p>{btn}</div>'
    sw = f'<div class="sw" style="color:{"#8AB4F8" if fc else BLUE}">Arraste →</div>' if i == 0 and n > 1 else ''
    brand = (f'<div class="brand" style="color:{t["brand"]}">{pin("#fff" if k=="cta" else RED, "#202124" if fc else t["bg"])}'
             f'Atualiza Brasil <span style="color:{"#fff" if k=="cta" else "#8AB4F8" if fc else BLUE}">360</span></div>')
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
