"""Exit gates for jhonalbert.com/lab (tier NONE build, 2026-09-16).

G1  mean rAF fps over a 15 s scripted wheel scroll at 1280x800, pass >= 55
G2  first-load bytes, pass <= 8 MB
G3  behaviour probes: scroll moves the object, hover flips the cursor, ES/EN swaps every string,
    WebGL disabled shows the still
Usage:  python tools/gates.py [--url http://127.0.0.1:8770/lab/] [--serve .output/public] [--headed]
Serves .output/public under the /lab/ prefix when --serve is given. Prints one JSON line per gate.
"""
import argparse, http.server, json, os, socketserver, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def serve(folder, port, prefix='/lab'):
    folder = str(folder)
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=folder, **k)
        def translate_path(self, path):
            p = path.split('?', 1)[0]
            if p == prefix or p == prefix + '/': p = '/index.html'
            elif p.startswith(prefix + '/'): p = p[len(prefix):]
            return super().translate_path(p)
        def log_message(self, *a): pass
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store'); super().end_headers()
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', port), H)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

def gpu_args():
    return ['--enable-gpu', '--use-angle=d3d11', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']

LAB = 'JSON.parse(document.documentElement.dataset.lab || "{}")'

def wait_ready(page):
    page.wait_for_function(f'({LAB}).ready === true', timeout=60_000)

def lab(page, key):
    return page.evaluate(f'({LAB}).{key}')

def g1_fps(p, url, headed):
    b = p.chromium.launch(headless=not headed, args=gpu_args())
    pg = b.new_page(viewport={'width': 1280, 'height': 800})
    pg.goto(url, wait_until='load'); wait_ready(pg)
    renderer = pg.evaluate("""() => { const c=document.createElement('canvas'); const gl=c.getContext('webgl'); const d=gl&&gl.getExtension('WEBGL_debug_renderer_info'); return d? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'n/a'; }""")
    pg.evaluate("""() => { window.__frames = 0; window.__t0 = performance.now(); const tick = () => { window.__frames++; requestAnimationFrame(tick); }; requestAnimationFrame(tick); }""")
    t0 = time.time(); direction = 1
    while time.time() - t0 < 15:
        pg.mouse.move(640, 400); pg.mouse.wheel(0, 140 * direction)
        pr = lab(pg, 'progress')
        if pr > 0.98: direction = -1
        if pr < 0.02: direction = 1
        pg.wait_for_timeout(60)
    frames, ms = pg.evaluate('[window.__frames, performance.now() - window.__t0]')
    fps = frames / (ms / 1000)
    b.close()
    return {'gate': 'G1', 'fps': round(fps, 1), 'renderer': renderer, 'pass': fps >= 55}

def g2_weight(p, url, headed):
    b = p.chromium.launch(headless=not headed, args=gpu_args())
    ctx = b.new_context(viewport={'width': 1280, 'height': 800})
    pg = ctx.new_page()
    total = 0; items = []
    def on_resp(r):
        nonlocal total
        try:
            body = r.body(); total += len(body); items.append((r.url.split('/')[-1][:48], len(body)))
        except Exception: pass
    pg.on('response', on_resp)
    pg.goto(url, wait_until='networkidle'); wait_ready(pg); pg.wait_for_timeout(1500)
    b.close()
    items.sort(key=lambda x: -x[1])
    return {'gate': 'G2', 'mb': round(total / 1048576, 2), 'files': len(items), 'biggest': items[:6], 'pass': total <= 8 * 1048576}

def g3_probes(p, url, headed):
    out = {}
    b = p.chromium.launch(headless=not headed, args=gpu_args())
    pg = b.new_page(viewport={'width': 1280, 'height': 800})
    pg.goto(url, wait_until='load'); wait_ready(pg)
    p0 = [lab(pg, 'progress'), lab(pg, 'rotY')]
    for _ in range(20): pg.mouse.move(640, 400); pg.mouse.wheel(0, 200); pg.wait_for_timeout(50)
    pg.wait_for_timeout(1200)
    p1 = [lab(pg, 'progress'), lab(pg, 'rotY')]
    out['scroll'] = {'before': p0, 'after': p1, 'pass': p1[0] > p0[0] + 0.2 and abs(p1[1] - p0[1]) > 0.05}
    hs = lab(pg, 'ringScreen')
    pg.mouse.move(hs['x'], hs['y']); pg.wait_for_timeout(400)
    cur = pg.evaluate('document.body.dataset.cursor || ""')
    pg.mouse.move(20, 20); pg.wait_for_timeout(400)
    cur_off = pg.evaluate('document.body.dataset.cursor || ""')
    out['hover'] = {'at': hs, 'cursor_on': cur, 'cursor_off': cur_off, 'pass': cur == 'pointer' and cur_off != 'pointer'}
    es = pg.evaluate('[...document.querySelectorAll("[data-i18n]")].map(e => e.textContent.trim())')
    pg.click('[data-lang-btn]'); pg.wait_for_timeout(300)
    en = pg.evaluate('[...document.querySelectorAll("[data-i18n]")].map(e => e.textContent.trim())')
    lang = pg.evaluate('document.documentElement.lang')
    same = [i for i, (a, c) in enumerate(zip(es, en)) if a == c]
    out['i18n'] = {'strings': len(es), 'unchanged': same, 'html_lang': lang, 'pass': len(es) > 0 and len(es) == len(en) and not same and lang == 'en'}
    b.close()
    b2 = p.chromium.launch(headless=not headed, args=['--disable-3d-apis'])
    pg2 = b2.new_page(viewport={'width': 1280, 'height': 800})
    pg2.goto(url, wait_until='load'); wait_ready(pg2); pg2.wait_for_timeout(500)
    fb = pg2.evaluate('(() => { const f = document.querySelector(".fallback"); return f ? getComputedStyle(f).display !== "none" && f.getBoundingClientRect().height > 0 : false; })()')
    webgl = lab(pg2, 'webgl')
    b2.close()
    out['fallback'] = {'visible': fb, 'webgl_flag': webgl, 'pass': fb and webgl is False}
    return {'gate': 'G3', **out, 'pass': all(v['pass'] for v in out.values())}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://127.0.0.1:8770/lab/')
    ap.add_argument('--serve', default='.output/public')
    ap.add_argument('--port', type=int, default=8770)
    ap.add_argument('--headed', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    httpd = serve(ROOT / a.serve, a.port) if a.serve else None
    from patchright.sync_api import sync_playwright
    results = []
    with sync_playwright() as p:
        for name, fn in [('G1', g1_fps), ('G2', g2_weight), ('G3', g3_probes)]:
            if a.only and name not in a.only: continue
            try:
                r = fn(p, a.url, a.headed)
            except Exception as e:
                r = {'gate': name, 'error': str(e)[:300], 'pass': False}
            print(json.dumps(r, ensure_ascii=False)); results.append(r)
    if httpd: httpd.shutdown()
    ok = all(r.get('pass') for r in results)
    print('ALL PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
