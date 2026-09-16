"""Capture the rendered coral as the WebGL-off fallback still (public/coral-still.webp).

Usage: python tools/still.py --url http://127.0.0.1:8771/lab/
Screenshots a 1040x1040 clip around the coral at 1280x800 (desktop layout), converts to WebP in-page.
"""
import argparse, base64
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://127.0.0.1:8771/lab/')
    ap.add_argument('--out', default='public/coral-still.webp')
    a = ap.parse_args()
    from patchright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=['--enable-gpu', '--use-angle=d3d11', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'])
        pg = b.new_page(viewport={'width': 1280, 'height': 800}, device_scale_factor=1)
        pg.goto(a.url, wait_until='load')
        pg.wait_for_function('JSON.parse(document.documentElement.dataset.lab || "{}").ready === true', timeout=60_000)
        pg.mouse.move(640, 400)
        pg.wait_for_timeout(2200)  # intro eased in
        # Hide DOM so the still is the object on the night background only.
        pg.add_style_tag(content='.dom, .top, .hotspot-label, .card { visibility: hidden !important }')
        pg.wait_for_timeout(200)
        png = pg.screenshot(clip={'x': 640 + 120 - 340, 'y': 400 - 340, 'width': 680, 'height': 680}, type='png')
        data = base64.b64encode(png).decode()
        webp = pg.evaluate("""async (data) => {
            const img = new Image(); img.src = 'data:image/png;base64,' + data; await img.decode();
            const c = document.createElement('canvas'); c.width = 680; c.height = 680;
            c.getContext('2d').drawImage(img, 0, 0);
            return c.toDataURL('image/webp', 0.86);
        }""", data)
        out = ROOT / a.out
        out.write_bytes(base64.b64decode(webp.split(',', 1)[1]))
        print('wrote', out, out.stat().st_size // 1024, 'KB')
        b.close()

if __name__ == '__main__':
    main()
