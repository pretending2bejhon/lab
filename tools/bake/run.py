"""Drive tools/bake/index.html headless and write the four lighting passes to public/textures/.

Usage:  python tools/bake/run.py [--model /public/models/coral.glb] [--size 2048] [--port 8765]
Serves the repo root over http (node_modules and public must resolve), opens the bake page with
patchright's Chromium, waits for window.__bakeDone, decodes the WebP data URLs.
"""
import argparse, base64, http.server, os, socketserver, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def serve(port):
    handler = http.server.SimpleHTTPRequestHandler
    class Quiet(handler):
        def log_message(self, *a): pass
    os.chdir(ROOT)
    httpd = socketserver.TCPServer(('127.0.0.1', port), Quiet)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='/public/models/coral.glb')
    ap.add_argument('--size', type=int, default=2048)
    ap.add_argument('--dilate', type=int, default=24)
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--out', default='public/textures')
    ap.add_argument('--headed', action='store_true')
    a = ap.parse_args()
    from patchright.sync_api import sync_playwright
    httpd = serve(a.port)
    outdir = ROOT / a.out
    outdir.mkdir(parents=True, exist_ok=True)
    url = f'http://127.0.0.1:{a.port}/tools/bake/index.html?model={a.model}&size={a.size}&dilate={a.dilate}'
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not a.headed, args=['--use-angle=default', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        page = browser.new_page(viewport={'width': 512, 'height': 512})
        logs = []
        page.on('console', lambda m: logs.append(m.text))
        page.goto(url, wait_until='load')
        page.wait_for_function('document.body.dataset.bakeDone === "1"', timeout=600_000)
        err = page.evaluate('document.body.dataset.bakeError || null')
        if err:
            print('BAKE ERROR:', err); print('\n'.join(logs)); sys.exit(1)
        names = [n for n in page.evaluate('document.body.dataset.passes || ""').split(',') if n]
        if not names:
            print('BAKE: no passes in the DOM'); print(page.evaluate('document.getElementById("log").textContent')); sys.exit(1)
        for name in names:
            data = page.evaluate(f'document.getElementById("pass-{name}").value')
            b = base64.b64decode(data.split(',', 1)[1])
            f = outdir / f'bake_{name}.webp'
            f.write_bytes(b)
            print(f'wrote {f} {len(b)//1024} KB')
        print('\n'.join(l for l in logs if l.startswith('[bake]')))
        browser.close()
    httpd.shutdown()
    print(f'done in {time.time()-t0:.1f}s')

if __name__ == '__main__':
    main()
