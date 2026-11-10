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

def ficha(s):
    """Ficha ilustrativa de um negocio num mapa (generica, sem marcas). s['estado']: 'antes' ou 'depois'."""
    antes = s.get('estado') == 'antes'
    nome, cat = esc(s.get('negocio') or 'Seu Negócio'), esc(s.get('categoria') or 'Padaria · Bairro')
    if antes:
        fotos = ('<div style="height:300px;background:#E8EAED;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#9AA0A6;font:500 30px R;gap:14px">'
                 '<svg width="90" height="72" viewBox="0 0 24 19"><path d="M3 4h4l2-3h6l2 3h4v14H3z" fill="none" stroke="#BDC1C6" stroke-width="1.6"/><circle cx="12" cy="11" r="4" fill="none" stroke="#BDC1C6" stroke-width="1.6"/><path d="M2 1l20 17" stroke="#BDC1C6" stroke-width="1.6"/></svg>Nenhuma foto</div>')
        rows = [('#9AA0A6', 'Horário não informado'), ('#9AA0A6', 'Telefone não informado'), (RED, 'Fechado permanentemente')]
        pill = f'<div style="margin-top:30px;display:inline-block;background:#FCE8E6;color:{RED};border-radius:30px;padding:14px 28px;font:500 28px R">Informações desatualizadas</div>'
    else:
        tile = lambda c1, c2, lab: (f'<div style="flex:1;background:linear-gradient(135deg,{c1},{c2});display:flex;align-items:flex-end;padding:18px;color:#fff;font:500 26px R">{lab}</div>')
        fotos = ('<div style="height:300px;display:flex;gap:6px">' + tile('#4285F4', '#1A73E8', 'Fachada') +
                 tile('#34A853', '#188038', 'Tour 360°') + tile('#FBBC04', '#E37400', 'Produtos') + '</div>')
        rows = [(GRN, 'Aberto agora · Fecha às 19:00'), (DARK, 'Telefone e WhatsApp atualizados'), (DARK, 'Fotos novas e tour 360°')]
        pill = f'<div style="margin-top:30px;display:inline-block;background:#E6F4EA;color:#188038;border-radius:30px;padding:14px 28px;font:500 28px R">Página completa e atualizada</div>'
    lines = ''.join(f'<div style="display:flex;align-items:center;gap:18px;margin-top:22px;font:400 32px R;color:{c}"><i style="width:14px;height:14px;border-radius:7px;background:{c};display:block"></i>{tx}</div>' for c, tx in rows)
    btns = ''.join(f'<span style="border:2px solid #DADCE0;border-radius:30px;padding:12px 26px;color:{BLUE};font:500 26px R">{b}</span>' for b in ('Rotas', 'Ligar', 'Site'))
    tag = (f'<div style="position:absolute;top:-28px;right:40px;background:{RED if antes else GRN};color:#fff;border-radius:30px;padding:12px 30px;font:700 28px R;letter-spacing:.06em">{"ANTES" if antes else "DEPOIS"}</div>')
    return (f'<div style="position:absolute;left:120px;right:120px;top:330px;background:#fff;border-radius:36px;box-shadow:0 8px 40px rgba(60,64,67,.22);overflow:visible">{tag}'
            f'<div style="border-radius:36px 36px 0 0;overflow:hidden">{fotos}</div>'
            f'<div style="padding:34px 44px 40px"><div style="display:flex;align-items:center;gap:16px">{pin(RED, "#fff", 34)}<span style="font:700 46px R;color:{DARK}">{nome}</span></div>'
            f'<div style="font:400 28px R;color:{GREY};margin-top:8px">{cat}</div>{lines}{pill}'
            f'<div style="display:flex;gap:16px;margin-top:30px;{"opacity:.35" if antes else ""}">{btns}</div></div></div>')

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
    elif k == 'ponto' and s['kind'] != 'mapa':
        col = ACC[(i - 1) % 4]
        body = f'<div class="c" style="top:{"620px" if fc else "220px"}"><div class="dot" style="background:{col}">{i}</div><h2 style="color:{t["fg"]};margin-top:56px">{esc(s["title"])}</h2><p style="color:{t["body"]};margin-top:44px">{esc(s.get("body"))}</p></div>'
    elif s['kind'] == 'mapa':
        body = f'<div class="c" style="top:110px"><h2 style="color:{t["fg"]};font-size:60px">{esc(s["title"])}</h2></div>' + ficha(s)
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
