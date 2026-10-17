"""Render Oracle post slides to PNG with the exact canvas renderer used by the page.
Needs: pip install playwright && python -m playwright install chromium
Usage: python3 render.py <post.json> <out_dir>   (post.json = {"slides":[...], "theme":"classic", "handle":"..."})
"""
import sys, json, re, base64, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
MASCOT = 'data:image/jpeg;base64,' + base64.b64encode((HERE/'mascot.jpg').read_bytes()).decode()
renderer = (HERE/'renderer.js').read_text()
F = HERE/'fonts'
faces = ''.join(
    f"@font-face{{font-family:Montserrat;font-weight:{w};src:url('data:font/woff2;base64,{base64.b64encode((F/f'montserrat-latin-{w}-normal.woff2').read_bytes()).decode()}') format('woff2')}}"
    for w in (600, 700, 800))

post = json.loads(pathlib.Path(sys.argv[1]).read_text())
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
html = f"""<!doctype html><html><head><meta charset=utf-8><style>{faces}</style></head><body><canvas id=c width=1080 height=1350></canvas>
<script>
const MASCOT={json.dumps(MASCOT)};
{renderer}
HANDLE={json.dumps(post.get('handle') or 'FOLLOW @ORACLE_SAINT_ADRIA')};
window.renderAll=async(slides,theme)=>{{await ready;const c=document.getElementById('c'),x=c.getContext('2d');const out=[];for(const s of slides){{render(x,s,theme);out.push(c.toDataURL('image/png'));}}return out;}};
</script></body></html>"""
page_file = out / '_render.html'
page_file.write_text(html)
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(page_file.as_uri()); pg.wait_for_timeout(500)
    urls = pg.evaluate('([s,t])=>renderAll(s,t)', [post['slides'], post.get('theme', 'classic')])
    fam = pg.evaluate("document.fonts.check('800 80px Montserrat')")
    br.close()
for i, u in enumerate(urls, 1):
    (out / f'{i}.png').write_bytes(base64.b64decode(u.split(',', 1)[1]))
page_file.unlink()
print(json.dumps({'slides': len(urls), 'montserrat': fam, 'errors': errs}))
