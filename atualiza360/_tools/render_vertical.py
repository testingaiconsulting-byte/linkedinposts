"""Stories e reels animados (1080x1920) da Atualiza Brasil 360, no mesmo estilo dos posts (render.py).

Uso:
  python3 atualiza360/_tools/render_vertical.py story <post.json> <pasta>   -> 01.jpg (um por slide: 01.jpg, 02.jpg, ...)
  python3 atualiza360/_tools/render_vertical.py reel  <post.json> <pasta>   -> reel.mp4 (H.264 + audio mudo) e capa.jpg

post.json = {"slides":[...]} com os mesmos slides dos posts: capa, ponto, cta, mapa; campos "estilo" e "destaque" como em render.py.
No reel cada slide e uma cena animada (texto a entrar palavra a palavra, numero e pontos a aparecer, ficha a subir);
cenas de ~3 a 4 s. O texto fica dentro da zona segura do Instagram (sem nada importante nos 250 px de cima e nos 420 de baixo).
Precisa de Playwright (Chromium) e ffmpeg com libx264 e aac.
"""
import json, sys, base64, os, re, shutil, subprocess, tempfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()

W, H, FPS = 1080, 1920, 30
BLUE, DARK, RED, YEL, GRN, GREY = '#1A73E8', '#202124', '#EA4335', '#FBBC04', '#34A853', '#5F6368'
ACC = [BLUE, RED, YEL, GRN]
DUR = {'capa': 3.4, 'ponto': 3.8, 'mapa': 4.2, 'cta': 3.6}

CSS = f"""@font-face{{font-family:R;src:url(data:font/ttf;base64,{b64(os.path.join(HERE, 'Roboto.ttf'))});font-weight:100 900}}
*{{margin:0;box-sizing:border-box}}body{{width:{W}px;height:{H}px;position:relative;overflow:hidden;font-family:R}}
#s{{position:absolute;inset:0}}
.strip{{position:absolute;left:0;right:0;top:0;height:16px;display:flex}}.strip i{{flex:1}}
.brand{{position:absolute;left:96px;top:250px;display:flex;align-items:center;gap:16px;font:700 36px R;letter-spacing:-.01em}}
.c{{position:absolute;left:96px;right:96px}}
.chip{{display:inline-flex;align-items:center;gap:12px;border:2px solid #DADCE0;border-radius:40px;padding:12px 28px 12px 20px;font:500 30px R}}
h1{{font:700 112px/1.07 R;letter-spacing:-.02em}} h2{{font:700 78px/1.12 R;letter-spacing:-.01em}}
p{{font:400 44px/1.5 R}}
.dot{{width:150px;height:150px;border-radius:75px;display:flex;align-items:center;justify-content:center;font:700 70px R;color:#fff}}
.dots{{display:flex;gap:16px;margin-top:70px}}.dots i{{width:26px;height:26px;border-radius:13px;display:block}}
.btn{{margin-top:70px;background:#fff;border-radius:70px;height:132px;display:flex;align-items:center;justify-content:center;font:500 44px R;box-shadow:0 2px 6px rgba(0,0,0,.18)}}
.w{{display:inline-block;white-space:pre}}
@keyframes up{{from{{opacity:0;transform:translateY(70px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{0%{{opacity:0;transform:scale(.2)}}70%{{opacity:1;transform:scale(1.12)}}100%{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(260px)}}to{{opacity:1;transform:none}}}}
@keyframes pulse{{0%,100%{{transform:none}}50%{{transform:scale(1.05)}}}}
@keyframes out{{from{{opacity:1;transform:none}}to{{opacity:0;transform:translateX(-90px)}}}}
.a{{animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.8,.2,1)}}"""

TH = {'capa': dict(bg='#FFFFFF', fg=DARK, body=GREY, brand=DARK),
      'ponto': dict(bg='#F8F9FA', fg=DARK, body='#3C4043', brand=DARK),
      'cta': dict(bg=BLUE, fg='#fff', body='#E8F0FE', brand='#fff')}
EST = {'azul': dict(capa=dict(bg='linear-gradient(160deg,#0B2E6F 0%,#1A4FB8 100%)', fg='#fff', body='#D2E3FC', brand='#fff'),
                    ponto=dict(bg='#E8F0FE', fg='#0B2E6F', body='#3C4043', brand='#0B2E6F'), cbg='#0B2E6F'),
       'amarelo': dict(capa=dict(bg='#FBBC04', fg=DARK, body='#3C2F00', brand=DARK),
                       ponto=dict(bg='#FEF7E0', fg=DARK, body='#3C4043', brand=DARK), cbg=BLUE),
       'verde': dict(capa=dict(bg='#188038', fg='#fff', body='#E6F4EA', brand='#fff'),
                     ponto=dict(bg='#E6F4EA', fg=DARK, body='#3C4043', brand=DARK), cbg='#188038')}

def esc(s): return (s or '').replace('&', '&amp;').replace('<', '&lt;')

def pin(color, hole, w=30):
    return (f'<svg width="{w}" height="{int(w*1.4)}" viewBox="0 0 30 42"><path d="M15 0C6.7 0 0 6.7 0 15c0 11.2 15 27 15 27s15-15.8 15-27C30 6.7 23.3 0 15 0z" fill="{color}"/>'
            f'<circle cx="15" cy="15" r="6" fill="{hole}"/></svg>')

def an(name, delay, dur=.6):
    return f'animation:{name} {dur}s {delay:.2f}s both cubic-bezier(.2,.8,.2,1)'

def words(text, t0, step=.07, destaque=''):
    """Titulo palavra a palavra; o pedaco 'destaque' fica numa caixa vermelha que salta no fim."""
    text = text or ''
    parts, out, t = [], [], t0
    if destaque and destaque in text:
        a, b = text.split(destaque, 1); parts = [(a, False), (destaque, True), (b, False)]
    else:
        parts = [(text, False)]
    hl_delay = None
    for seg, hl in parts:
        if hl:
            hl_delay = t
            out.append(f'<span class="w" style="background:{RED};color:#fff;border-radius:16px;padding:0 18px;{an("pop", t + .15, .55)}">{esc(seg)}</span>')
            t += step * len(seg.split())
            continue
        for tok in re.split(r'(\s+)', seg):
            if not tok: continue
            if tok.isspace(): out.append(tok); continue
            out.append(f'<span class="w" style="{an("up", t)}">{esc(tok)}</span>'); t += step
    return ''.join(out), t

def ficha(s, t0):
    antes = s.get('estado') == 'antes'
    nome, cat = esc(s.get('negocio') or 'Seu Negócio'), esc(s.get('categoria') or 'Padaria · Bairro')
    if antes:
        fotos = ('<div style="height:340px;background:#E8EAED;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#9AA0A6;font:500 34px R;gap:16px">'
                 '<svg width="100" height="80" viewBox="0 0 24 19"><path d="M3 4h4l2-3h6l2 3h4v14H3z" fill="none" stroke="#BDC1C6" stroke-width="1.6"/><circle cx="12" cy="11" r="4" fill="none" stroke="#BDC1C6" stroke-width="1.6"/><path d="M2 1l20 17" stroke="#BDC1C6" stroke-width="1.6"/></svg>Nenhuma foto</div>')
        rows = [('#9AA0A6', 'Horário não informado'), ('#9AA0A6', 'Telefone não informado'), (RED, 'Fechado permanentemente')]
        pill = ('#FCE8E6', RED, 'Informações desatualizadas')
    else:
        tile = lambda c1, c2, lab: f'<div style="flex:1;background:linear-gradient(135deg,{c1},{c2});display:flex;align-items:flex-end;padding:20px;color:#fff;font:500 30px R">{lab}</div>'
        fotos = '<div style="height:340px;display:flex;gap:6px">' + tile('#4285F4', '#1A73E8', 'Fachada') + tile('#34A853', '#188038', 'Tour 360°') + tile('#FBBC04', '#E37400', 'Produtos') + '</div>'
        rows = [(GRN, 'Aberto agora · Fecha às 19:00'), (DARK, 'Telefone e WhatsApp atualizados'), (DARK, 'Fotos novas e tour 360°')]
        pill = ('#E6F4EA', '#188038', 'Página completa e atualizada')
    lines = ''.join(f'<div style="display:flex;align-items:center;gap:20px;margin-top:26px;font:400 38px R;color:{c};{an("up", t0 + .6 + j*.25)}"><i style="width:16px;height:16px;border-radius:8px;background:{c};display:block"></i>{tx}</div>'
                    for j, (c, tx) in enumerate(rows))
    tag = f'<div style="position:absolute;top:-34px;right:44px;background:{RED if antes else GRN};color:#fff;border-radius:34px;padding:14px 34px;font:700 32px R;letter-spacing:.06em;{an("pop", t0 + .35, .5)}">{"ANTES" if antes else "DEPOIS"}</div>'
    return (f'<div class="c" style="top:720px;left:80px;right:80px;background:#fff;border-radius:40px;box-shadow:0 8px 40px rgba(60,64,67,.25);{an("rise", t0, .7)}">{tag}'
            f'<div style="border-radius:40px 40px 0 0;overflow:hidden">{fotos}</div>'
            f'<div style="padding:40px 48px 48px"><div style="display:flex;align-items:center;gap:18px">{pin(RED, "#fff", 38)}<span style="font:700 52px R;color:{DARK}">{nome}</span></div>'
            f'<div style="font:400 32px R;color:{GREY};margin-top:10px">{cat}</div>{lines}'
            f'<div style="margin-top:34px;display:inline-block;background:{pill[0]};color:{pill[1]};border-radius:34px;padding:16px 32px;font:500 32px R;{an("pop", t0 + 1.5, .5)}">{pill[2]}</div></div></div>')

def scene(s, i, dur, saida=True, num=None):
    k = s['kind'] if s['kind'] in ('capa', 'ponto', 'cta', 'mapa') else 'ponto'
    tk = 'ponto' if k == 'mapa' else k
    t = dict(TH[tk]); es = EST.get(s.get('estilo') or '')
    if es and tk in ('capa', 'ponto'): t.update(es[tk])
    if es and tk == 'cta': t['bg'] = es['cbg']
    dark_bg = (tk == 'cta') or (bool(es) and tk == 'capa' and s.get('estilo') != 'amarelo')
    solid = t['bg'] if t['bg'].startswith('#') else '#0B2E6F'
    strip = '' if tk == 'cta' else '<div class="strip">' + ''.join(f'<i style="background:{c}"></i>' for c in ACC) + '</div>'
    brand = (f'<div class="brand" style="color:{t["brand"]};{an("fade", .05, .5)}">{pin("#fff" if dark_bg else RED, solid if dark_bg else ("#fff" if tk == "capa" and not es else solid))}'
             f'Atualiza Brasil <span style="color:{"#fff" if dark_bg else BLUE}">360</span></div>')
    if k == 'capa':
        eb = (f'<div style="{an("up", .1)}"><span class="chip" style="color:{t["body"]};border-color:{"rgba(255,255,255,.4)" if dark_bg else "#DADCE0"}">{pin(RED, "#fff", 24)}{esc(s.get("eyebrow"))}</span></div>'
              if s.get('eyebrow') else '')
        tw, te = words(s.get('title'), .35, destaque=s.get('destaque') or '')
        dots = '<div class="dots">' + ''.join(f'<i style="background:{DARK if (c == YEL and s.get("estilo") == "amarelo") else c};{an("pop", te + .1 + j*.08, .4)}"></i>' for j, c in enumerate(ACC)) + '</div>'
        body = (f'<div class="c" style="top:560px">{eb}<h1 style="color:{t["fg"]};margin-top:{60 if eb else 0}px">{tw}</h1>{dots}'
                f'<p style="color:{t["body"]};margin-top:60px;{an("up", te + .45)}">{esc(s.get("body"))}</p></div>')
    elif k == 'ponto':
        num = num or i
        col = ACC[(num - 1) % 4]
        tw, te = words(s.get('title'), .45)
        body = (f'<div class="c" style="top:620px"><div class="dot" style="background:{col};{an("pop", .1, .55)}">{num}</div>'
                f'<h2 style="color:{t["fg"]};margin-top:70px">{tw}</h2><p style="color:{t["body"]};margin-top:54px;{an("up", te + .3)}">{esc(s.get("body"))}</p></div>')
    elif k == 'mapa':
        tw, _ = words(s.get('title'), .15)
        body = f'<div class="c" style="top:470px"><h2 style="color:{t["fg"]};font-size:68px">{tw}</h2></div>' + ficha(s, .55)
    else:
        tw, te = words(s.get('title'), .4)
        btn = (f'<div class="btn" style="color:{solid};{an("pop", te + .5, .5)}"><span style="display:inline-block;animation:pulse 1.2s {te + 1.1:.2f}s 2 ease-in-out">{esc(s.get("button"))}</span></div>'
               if s.get('button') else '')
        body = (f'<div class="c" style="top:600px"><div style="{an("pop", .1, .5)}">{pin("#fff", solid, 64)}</div><h1 style="color:{t["fg"]};font-size:100px;margin-top:46px">{tw}</h1>'
                f'<p style="color:{t["body"]};margin-top:56px;{an("up", te + .25)}">{esc(s.get("body"))}</p>{btn}</div>')
    out = f'animation:out .35s {dur - .35:.2f}s both ease-in' if saida else ''
    return (f'<html><head><meta charset=utf-8><style>{CSS}</style></head><body style="background:{t["bg"]}">'
            f'{strip}<div id="s" style="{out}">{brand}{body}</div></body></html>')

SEEK = "t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; })"

def main():
    modo, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    sl = json.load(open(src))['slides']; os.makedirs(out, exist_ok=True)
    nums, c = [], 0
    for s in sl:
        if s.get('kind') not in ('capa', 'cta', 'mapa'): c += 1
        nums.append(c or None)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': H})
        if modo == 'story':
            for i, s in enumerate(sl):
                pg.set_content(scene(s, i, 99, saida=False, num=nums[i])); pg.wait_for_timeout(200)
                pg.evaluate(SEEK, 30); pg.screenshot(path=f'{out}/{i+1:02d}.jpg', type='jpeg', quality=92)
        elif modo == 'reel':
            tmp = tempfile.mkdtemp(); n = 0
            for i, s in enumerate(sl):
                k = s['kind'] if s['kind'] in DUR else 'ponto'
                dur = DUR[k] + (0.8 if i == len(sl) - 1 else 0)
                pg.set_content(scene(s, i, dur, saida=i < len(sl) - 1, num=nums[i])); pg.wait_for_timeout(250)
                for f in range(int(round(dur * FPS))):
                    pg.evaluate(SEEK, f / FPS)
                    pg.screenshot(path=f'{tmp}/{n:05d}.jpg', type='jpeg', quality=90); n += 1
                if i == 0:
                    pg.evaluate(SEEK, dur - .4); pg.screenshot(path=f'{out}/capa.jpg', type='jpeg', quality=92)
            total = n / FPS
            subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%05d.jpg',
                            '-f', 'lavfi', '-t', f'{total:.3f}', '-i', 'anullsrc=r=44100:cl=stereo',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p',
                            '-r', str(FPS), '-b:v', '5M', '-maxrate', '6M', '-bufsize', '10M', '-c:a', 'aac', '-b:a', '128k',
                            '-movflags', '+faststart', '-shortest', f'{out}/reel.mp4'], check=True)
            shutil.rmtree(tmp)
            print(f'reel {len(sl)} cenas, {total:.1f}s')
        else:
            sys.exit('modo: story ou reel')
        b.close()
    print(sorted(os.listdir(out)))

if __name__ == '__main__':
    main()
