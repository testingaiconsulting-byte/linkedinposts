"""Reels com animação a sério (e stories) em 1080x1920, com a identidade de cada marca.

Uso:
  python3 _shared/anim_reel.py reel  <marca> <post.json> <pasta>   -> reel.mp4 + capa.jpg
  python3 _shared/anim_reel.py story <marca> <post.json> <pasta>   -> story.jpg (1.º slide)
  marca: novoclick | koobings | oraculo
  post.json = {"slides":[...], "musica": "<ficheiro opcional>", "inicio": 0}

Cenas (campo "kind" de cada slide; os slides de feed de cada marca também são aceites e convertidos):
  capa      {eyebrow, title, body}                    título entra palavra a palavra
  numero    {stat:"80%"|"30 NOV"|"3", title, body}    o número conta a subir até ao valor
  prazo     = numero (data/prazo)
  problema  {title:<problema>, solucao:<resposta>, body}  o problema aparece, é riscado e a solução entra por cima
  ponto     {title, body}                             número do passo salta, texto entra
  lista     {title, items:[{"t","ok":true|false,"note"}]}  itens entram um a um com ✓ ou ✗
  placar    {teamA, scoreA, teamB, scoreB, head, kicker}  equipas entram dos lados, golos contam
  cta       {title, body, button}                     botão pulsa
Campo opcional "estilo": "escuro" | "claro" | "cor" (fundo da cena). Barra de progresso no topo, formas de fundo em
movimento, saída de cada cena a deslizar. Música opcional, senão áudio mudo. Precisa de Playwright e ffmpeg.
"""
import json, sys, base64, os, re, shutil, subprocess, tempfile, html as H
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, HH, FPS = 1080, 1920, 30
def b64(p): return base64.b64encode(open(os.path.join(ROOT, p), 'rb').read()).decode()
def esc(s): return H.escape(str(s or ''), quote=False)

BRANDS = {
    'novoclick': dict(
        fonts=[('Hd', 'render/fonts/Archivo.ttf', 'truetype'), ('Bd', 'render/fonts/IBMPlexSans.ttf', 'truetype')],
        escuro=dict(bg='#2B2E33', fg='#FFFFFF', sub='#D2D3D5', acc='#7DD49F', logo='novoclick/_tools/logo_dark.png'),
        claro=dict(bg='#F3F5F2', fg='#2E3235', sub='#55595C', acc='#2E9E4A', logo='novoclick/_tools/logo_light.png'),
        cor=dict(bg='#2E9E4A', fg='#FFFFFF', sub='#EEF8F1', acc='#FFFFFF', logo='novoclick/_tools/logo_green.png'),
        ok='#2E9E4A', bad='#E5533D', btn='Envie-nos mensagem', head_w=800, upper=False,
        labels=('O PROBLEMA', 'COMO RESOLVER'), foot=''),
    'koobings': dict(
        fonts=[('Hd', 'koobings/_tools/Inter.ttf', 'truetype'), ('Bd', 'koobings/_tools/Inter.ttf', 'truetype')],
        escuro=dict(bg='#0036CC', fg='#FFFFFF', sub='#DCE6FF', acc='#FFCB1A', word='#FFFFFF'),
        claro=dict(bg='#EEF3FF', fg='#111111', sub='#3A3F4B', acc='#0044FF', word='#0044FF'),
        cor=dict(bg='#FFCB1A', fg='#111111', sub='#3A3000', acc='#0036CC', word='#111111'),
        ok='#12A150', bad='#E5533D', btn='1 mês grátis · link na bio', head_w=800, upper=False,
        labels=('ANTES', 'COM A KOOBINGS'), foot='', wordmark='koobings'),
    'oraculo': dict(
        fonts=[('Hd', 'oracle-saint-adria/_tools/fonts/montserrat-latin-800-normal.woff2', 'woff2'),
               ('Bd', 'oracle-saint-adria/_tools/fonts/montserrat-latin-600-normal.woff2', 'woff2')],
        escuro=dict(bg='#0A100C', fg='#FFFFFF', sub='#E6C79C', acc='#BF8448', avatar='oracle-saint-adria/_tools/mascot.jpg'),
        claro=dict(bg='#0F2F1A', fg='#FFFFFF', sub='#E6C79C', acc='#E6C79C', avatar='oracle-saint-adria/_tools/mascot.jpg'),
        cor=dict(bg='#BF8448', fg='#0A100C', sub='#2A1A08', acc='#0A100C', avatar='oracle-saint-adria/_tools/mascot.jpg'),
        ok='#4CC27A', bad='#E5533D', btn='SEGUE @ORACLE_SAINT_ADRIA', head_w=800, upper=True,
        labels=('O BOLETIM', 'A REALIDADE'), foot='18+ · JOGA COM RESPONSABILIDADE', handle='@oracle_saint_adria'),
}
DEF_TONE = {'capa': 'escuro', 'numero': 'cor', 'prazo': 'cor', 'problema': 'claro', 'ponto': 'claro', 'lista': 'escuro', 'placar': 'escuro', 'cta': 'cor'}
DUR = {'capa': 3.3, 'numero': 3.8, 'prazo': 3.8, 'problema': 5.0, 'ponto': 3.5, 'placar': 4.2, 'cta': 3.6}

def normalize(s, brand):
    """Converte slides de feed das marcas para as cenas."""
    s = dict(s); k = s.get('kind') or s.get('tpl') or 'ponto'
    if k == 'statement': s.update(kind='capa', title=s.get('head'), body=s.get('sub'), eyebrow=s.get('kicker'))
    elif k == 'score': s.update(kind='placar')
    elif k == 'list':
        s.update(kind='lista', eyebrow=s.get('kicker'),
                 items=[{'t': l.get('t'), 'ok': {'+': True, 'x': False}.get(l.get('mark')), 'note': l.get('note')} for l in s.get('lines', [])])
    elif k == 'frase': s.update(kind='capa')
    elif k == 'prazo': s.update(kind='numero')
    elif k not in ('capa', 'numero', 'problema', 'ponto', 'lista', 'placar', 'cta'): s['kind'] = 'ponto'
    return s

def split_num(stat):
    m = re.match(r'^(\D*?)(\d{1,3}(?:\.\d{3})+|\d+)(.*)$', str(stat or '').strip())
    if not m: return None
    pre, num, suf = m.groups(); thou = '.' in num
    return pre, int(num.replace('.', '')), suf, thou

def css(b):
    ff = ''.join(f"@font-face{{font-family:{n};src:url(data:font/{t};base64,{b64(p)}) format('{t}')}}" for n, p, t in b['fonts'])
    tt = 'text-transform:uppercase;' if b['upper'] else ''
    return ff + f"""*{{margin:0;box-sizing:border-box}}body{{width:{W}px;height:{HH}px;position:relative;overflow:hidden;font-family:Bd}}
#s{{position:absolute;inset:0}}
.blob{{position:absolute;border-radius:50%;opacity:.13}}
.top{{position:absolute;left:96px;right:96px;top:222px;display:flex;align-items:center;gap:18px;font:600 32px Bd}}
.prog{{position:absolute;left:96px;right:96px;top:150px;display:flex;gap:10px}}.prog i{{flex:1;height:8px;border-radius:4px;overflow:hidden;position:relative}}.prog b{{position:absolute;inset:0;transform-origin:left}}
.c{{position:absolute;left:96px;right:96px}}
.eb{{font:600 30px Bd;letter-spacing:.14em;text-transform:uppercase}}
h1{{font:{b['head_w']} 118px/1.04 Hd;letter-spacing:-.02em;{tt}}} h2{{font:{b['head_w']} 82px/1.1 Hd;letter-spacing:-.01em;{tt}}}
p{{font:400 44px/1.5 Bd}}
.w{{display:inline-block;white-space:pre}}
.big{{font:{b['head_w']} 300px/0.95 Hd;letter-spacing:-.04em}}
.badge{{display:inline-flex;align-items:center;gap:14px;border-radius:50px;padding:14px 30px;font:700 30px Bd;letter-spacing:.1em}}
.card{{border-radius:36px;padding:44px 48px;position:relative}}
.strike{{position:absolute;left:30px;right:30px;top:50%;height:10px;border-radius:5px;transform-origin:left}}
.item{{display:flex;align-items:center;gap:28px;padding:26px 0;font:{b['head_w']} 54px/1.15 Hd;{tt}}}
.ic{{width:76px;height:76px;border-radius:38px;flex:none;display:flex;align-items:center;justify-content:center}}
.btn{{margin-top:70px;border-radius:70px;height:136px;display:flex;align-items:center;justify-content:center;font:700 44px Bd}}
.foot{{position:absolute;left:0;right:0;top:1640px;text-align:center;font:600 26px Bd;letter-spacing:.08em}}
@keyframes up{{from{{opacity:0;transform:translateY(80px)}}to{{opacity:1;transform:none}}}}
@keyframes left{{from{{opacity:0;transform:translateX(-160px)}}to{{opacity:1;transform:none}}}}
@keyframes right{{from{{opacity:0;transform:translateX(160px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{0%{{opacity:0;transform:scale(.2)}}65%{{opacity:1;transform:scale(1.15)}}100%{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes dim{{to{{opacity:.35}}}}
@keyframes wipe{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes pulse{{0%,100%{{transform:none}}50%{{transform:scale(1.06)}}}}
@keyframes shake{{0%,100%{{transform:none}}20%{{transform:translateX(-14px)}}40%{{transform:translateX(12px)}}60%{{transform:translateX(-8px)}}80%{{transform:translateX(5px)}}}}
@keyframes drift1{{from{{transform:translate(0,0)}}to{{transform:translate(-120px,160px)}}}}
@keyframes drift2{{from{{transform:translate(0,0)}}to{{transform:translate(140px,-120px)}}}}
@keyframes out{{from{{opacity:1;transform:none}}to{{opacity:0;transform:translateX(-120px)}}}}"""

def an(name, d, dur=.6, ease='cubic-bezier(.2,.8,.2,1)'):
    return f'animation:{name} {dur}s {d:.2f}s both {ease}'

def words(text, t0, b, step=.075, hl=None):
    text = (text or '').upper() if b['upper'] else (text or '')
    out, t = [], t0
    for tok in re.split(r'(\s+)', text):
        if not tok: continue
        if tok.isspace(): out.append(tok); continue
        out.append(f'<span class="w" style="{an("up", t)}">{esc(tok)}</span>'); t += step
    return ''.join(out), t

CHECK = '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
CROSS = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>'

def header(b, t, n, i, total_scenes):
    if 'logo' in t: who = f'<img src="data:image/png;base64,{b64(t["logo"])}" style="height:76px">'
    elif 'avatar' in t:
        who = (f'<img src="data:image/jpeg;base64,{b64(t["avatar"])}" style="width:76px;height:76px;border-radius:38px;object-fit:cover;border:3px solid {t["acc"]}">'
               f'<span style="color:{t["fg"]}">{esc(b["handle"])}</span>')
    else: who = f'<span style="font:800 50px Hd;letter-spacing:-.02em;color:{t["word"]}">{esc(b["wordmark"])}</span>'
    return f'<div class="top" style="{an("fade", .05, .4)}">{who}</div>'

def progress(t, idx, n, dur):
    bars = []
    for j in range(n):
        fill = 'transform:scaleX(1)' if j < idx else (f'transform:scaleX(0);{an("wipe", 0, dur, "linear")}' if j == idx else 'transform:scaleX(0)')
        bars.append(f'<i style="background:{t["fg"]}33"><b style="background:{t["fg"]};{fill}"></b></i>')
    return '<div class="prog">' + ''.join(bars) + '</div>'

def scene(b, s, idx, n, dur, saida, num):
    k = s['kind']; tone = s.get('estilo') if s.get('estilo') in ('escuro', 'claro', 'cor') else DEF_TONE[k]
    t = b[tone]; fg, sub, acc = t['fg'], t['sub'], t['acc']
    blobs = (f'<div class="blob" style="width:760px;height:760px;right:-260px;top:-160px;background:{acc};{an("drift1", 0, 7, "ease-in-out")}"></div>'
             f'<div class="blob" style="width:560px;height:560px;left:-220px;bottom:-120px;background:{acc};{an("drift2", 0, 7, "ease-in-out")}"></div>')
    cnt = ''
    if k == 'capa':
        eb = f'<div class="eb" style="color:{acc};{an("left", .1)}">{esc(s.get("eyebrow"))}</div>' if s.get('eyebrow') else ''
        tw, te = words(s.get('title'), .3, b)
        body = (f'<div class="c" style="top:640px">{eb}<h1 style="color:{fg};margin-top:{50 if eb else 0}px">{tw}</h1>'
                f'<div style="width:140px;height:12px;border-radius:6px;background:{acc};margin-top:60px;transform-origin:left;{an("wipe", te + .05, .5)}"></div>'
                f'<p style="color:{sub};margin-top:50px;{an("up", te + .3)}">{esc(s.get("body"))}</p></div>')
    elif k == 'numero':
        sn = split_num(s.get('stat'))
        if sn:
            pre, to, suf, thou = sn
            big = (f'<div class="big" style="color:{acc};{an("pop", .15, .5)}">{esc(pre)}<span data-count data-to="{to}" data-d=".2" data-dur="1.4" data-thou="{int(thou)}">0</span>'
                   f'<span style="font-size:.55em">{esc(suf)}</span></div>')
        else:
            big = f'<div class="big" style="color:{acc};font-size:200px;{an("pop", .15, .55)}">{esc(s.get("stat"))}</div>'
        tw, te = words(s.get('title'), 1.45, b)
        eb = f'<div class="eb" style="color:{sub};margin-bottom:30px;{an("left", .05)}">{esc(s.get("eyebrow"))}</div>' if s.get('eyebrow') else ''
        body = (f'<div class="c" style="top:600px">{eb}{big}<h2 style="color:{fg};margin-top:60px">{tw}</h2>'
                f'<p style="color:{sub};margin-top:44px;{an("up", te + .25)}">{esc(s.get("body"))}</p></div>')
    elif k == 'problema':
        l1, l2 = s.get('labels') or b['labels']
        prob = (s.get('title') or '').upper() if b['upper'] else s.get('title')
        sol = (s.get('solucao') or s.get('body') or '')
        sol = sol.upper() if b['upper'] else sol
        body = (f'<div class="c" style="top:540px">'
                f'<div class="badge" style="background:{b["bad"]};color:#fff;{an("pop", .1, .45)}">{CROSS}{esc(l1)}</div>'
                f'<div class="card" style="margin-top:34px;background:{fg}14;{an("up", .25)}"><div style="{an("dim", 1.7, .4)}">'
                f'<h2 style="color:{fg};font-size:68px;{an("shake", 1.25, .45, "ease-in-out")}">{esc(prob)}</h2></div>'
                f'<div class="strike" style="background:{b["bad"]};transform:scaleX(0);{an("wipe", 1.3, .45)}"></div></div>'
                f'<div class="badge" style="margin-top:70px;background:{b["ok"]};color:#fff;{an("pop", 2.0, .45)}">{CHECK}{esc(l2)}</div>'
                f'<div class="card" style="margin-top:34px;background:{b["ok"]};{an("up", 2.2, .6)}">'
                f'<h2 style="color:#fff;font-size:64px">{esc(sol)}</h2></div>'
                + (f'<p style="color:{sub};margin-top:44px;{an("up", 2.9)}">{esc(s.get("body"))}</p>' if s.get('solucao') and s.get('body') else '') +
                '</div>')
    elif k == 'ponto':
        tw, te = words(s.get('title'), .45, b)
        body = (f'<div class="c" style="top:640px"><div style="width:170px;height:170px;border-radius:85px;background:{acc};color:{t["bg"]};display:flex;align-items:center;justify-content:center;font:{b["head_w"]} 84px Hd;{an("pop", .1, .55)}">{num}</div>'
                f'<h2 style="color:{fg};margin-top:70px">{tw}</h2><p style="color:{sub};margin-top:50px;{an("up", te + .25)}">{esc(s.get("body"))}</p></div>')
    elif k == 'lista':
        items = s.get('items') or []
        rows = []
        for j, it in enumerate(items[:6]):
            d = .9 + j * .6
            ok = it.get('ok')
            ic = (f'<div class="ic" style="background:{b["ok"] if ok else b["bad"] if ok is False else acc};{an("pop", d + .3, .4)}">{CHECK if ok else CROSS if ok is False else ""}</div>')
            note = f'<span style="margin-left:auto;font:600 40px Bd;color:{sub};{an("fade", d + .45, .4)}">{esc(it.get("note"))}</span>' if it.get('note') else ''
            txt = (it.get('t') or '').upper() if b['upper'] else it.get('t')
            rows.append(f'<div class="item" style="color:{fg};border-bottom:2px solid {fg}22;{an("left", d, .5)}">{ic}<span>{esc(txt)}</span>{note}</div>')
        eb = f'<div class="eb" style="color:{acc};{an("left", .05)}">{esc(s.get("eyebrow"))}</div>' if s.get('eyebrow') else ''
        tw, _ = words(s.get('title'), .2, b)
        body = f'<div class="c" style="top:560px">{eb}<h2 style="color:{fg};margin:30px 0 30px">{tw}</h2>{"".join(rows)}</div>'
    elif k == 'placar':
        def team(name, score, side, d):
            sc = split_num(score)
            num_html = (f'<span data-count data-to="{sc[1]}" data-d="{d + .5}" data-dur=".9" data-thou="0">0</span>' if sc else esc(score))
            return (f'<div style="display:flex;align-items:center;justify-content:space-between;padding:30px 0;border-bottom:3px solid {acc}55;{an(side, d, .6)}">'
                    f'<span style="font:{b["head_w"]} 76px Hd;color:{fg};text-transform:uppercase">{esc(name)}</span>'
                    f'<span style="font:{b["head_w"]} 150px Hd;color:{acc}">{num_html}</span></div>')
        eb = f'<div class="badge" style="background:{acc};color:{t["bg"]};{an("pop", .05, .45)}">{esc(s.get("kicker") or "")}</div>' if s.get('kicker') else ''
        tw, _ = words(s.get('head'), 2.0, b, step=.06)
        body = (f'<div class="c" style="top:560px">{eb}<div style="margin-top:40px">{team(s.get("teamA"), s.get("scoreA"), "left", .3)}{team(s.get("teamB"), s.get("scoreB"), "right", .55)}</div>'
                f'<h2 style="color:{fg};font-size:64px;margin-top:60px">{tw}</h2></div>')
    else:  # cta
        tw, te = words(s.get('title'), .35, b)
        btn = s.get('button') or b['btn']
        body = (f'<div class="c" style="top:680px"><h1 style="color:{fg};font-size:104px">{tw}</h1>'
                f'<p style="color:{sub};margin-top:56px;{an("up", te + .2)}">{esc(s.get("body"))}</p>'
                f'<div class="btn" style="background:{fg};color:{t["bg"]};{an("pop", te + .5, .5)}"><span style="display:inline-block;animation:pulse 1.1s {te + 1.1:.2f}s 3 ease-in-out">{esc(btn)}</span></div></div>')
    foot = f'<div class="foot" style="color:{sub}">{esc(b["foot"])}</div>' if b['foot'] else ''
    out = f'animation:out .35s {dur - .35:.2f}s both ease-in' if saida else ''
    return (f'<html><head><meta charset=utf-8><style>{css(b)}</style></head><body style="background:{t["bg"]}">{blobs}'
            f'{progress(t, idx, n, dur) if n > 1 else ""}<div id="s" style="{out}">{header(b, t, n, idx, n)}{body}{foot}</div>'
            f'<script>window.tick=function(t){{document.getAnimations().forEach(function(a){{a.pause();a.currentTime=t*1000;}});'
            f'document.querySelectorAll("[data-count]").forEach(function(e){{var d=+e.dataset.d,u=+e.dataset.dur,to=+e.dataset.to;'
            f'var p=Math.max(0,Math.min(1,(t-d)/u));p=1-Math.pow(1-p,3);var v=Math.round(to*p);var s=String(v);'
            f'if(e.dataset.thou=="1")s=s.replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".");e.textContent=s;}});}};</script></body></html>')

def dur_of(s):
    if s['kind'] == 'lista': return 1.9 + .6 * min(6, len(s.get('items') or []))
    return DUR[s['kind']]

def main():
    modo, marca, src, out = sys.argv[1:5]
    b = BRANDS[marca]; post = json.load(open(src))
    sl = [normalize(s, b) for s in post['slides']]
    if modo == 'story': sl = sl[:1]
    os.makedirs(out, exist_ok=True)
    nums, c = [], 0
    for s in sl:
        if s['kind'] == 'ponto': c += 1
        nums.append(c)
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width': W, 'height': HH})
        if modo == 'story':
            pg.set_content(scene(b, sl[0], 0, 1, 99, False, 1)); pg.wait_for_timeout(300)
            pg.evaluate('t=>window.tick(t)', 20); pg.screenshot(path=f'{out}/story.jpg', type='jpeg', quality=92)
        else:
            tmp = tempfile.mkdtemp(); fr = 0
            for i, s in enumerate(sl):
                d = dur_of(s) + (.8 if i == len(sl) - 1 else 0)
                pg.set_content(scene(b, s, i, len(sl), d, i < len(sl) - 1, nums[i] or 1)); pg.wait_for_timeout(300)
                for f in range(int(round(d * FPS))):
                    pg.evaluate('t=>window.tick(t)', f / FPS)
                    pg.screenshot(path=f'{tmp}/{fr:05d}.jpg', type='jpeg', quality=90); fr += 1
                if i == 0:
                    pg.evaluate('t=>window.tick(t)', d - .45); pg.screenshot(path=f'{out}/capa.jpg', type='jpeg', quality=92)
            total = fr / FPS
            mus = post.get('musica')
            audio = (['-ss', str(post.get('inicio') or 0), '-i', mus] if mus else ['-f', 'lavfi', '-t', f'{total:.3f}', '-i', 'anullsrc=r=44100:cl=stereo'])
            af = ['-af', f'atrim=duration={total:.3f},afade=t=in:d=.6,afade=t=out:st={max(0, total - 1.2):.3f}:d=1.2'] if mus else []
            subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%05d.jpg'] + audio + af +
                           ['-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p',
                            '-r', str(FPS), '-b:v', '5M', '-maxrate', '6M', '-bufsize', '10M', '-c:a', 'aac', '-b:a', '128k', '-ac', '2',
                            '-movflags', '+faststart', '-t', f'{total:.3f}', f'{out}/reel.mp4'], check=True)
            shutil.rmtree(tmp); print(f'reel {len(sl)} cenas, {total:.1f}s')
        br.close()
    print(sorted(os.listdir(out)))

if __name__ == '__main__':
    main()
