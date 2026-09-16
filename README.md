# lab

3D layer tests for jhonalbert.com. Served at https://jhonalbert.com/lab/ from the `gh-pages` branch.

Stack: Nuxt (static export) + three.js + GSAP ScrollTrigger + Lenis. One CC0 coral (Smithsonian NMNH,
*Corallium sp.*, USNM 56807) with four baked lighting passes cross-faded by scroll and pointer.

## Run

```
npm install
npx nuxi dev            # http://localhost:3000/lab/
npx nuxi generate       # .output/public
bash tools/deploy.sh "message"   # pushes .output/public to gh-pages
```

## Asset pipeline (reproducible)

```
# 1. source model (CC0), not committed
curl -L -o tools/coral-src.glb "https://3d-api.si.edu/content/document/3d_package:7fd1cb15-599b-44e5-8a14-579dfb749434/USNM_56807-150k-2048-medium.glb"
# 2. quarter the faces, keep the 2048 albedo for baking
npx gltf-transform simplify tools/coral-src.glb tools/coral-simp.glb --ratio 0.25 --error 0.0008
npx gltf-transform resize tools/coral-simp.glb tools/coral-res.glb --width 2048 --height 2048
# 3. runtime model: geometry + UVs only, Draco
node tools/strip-textures.mjs tools/coral-res.glb tools/coral-geo.glb
npx gltf-transform draco tools/coral-geo.glb public/models/coral.glb --method edgebreaker
# 4. bake TL / TR / BL / BR lighting passes into UV space (headless Chromium via patchright)
MSYS_NO_PATHCONV=1 python tools/bake/run.py --model /tools/coral-res.glb --size 2048 --dilate 24
# 5. fallback still (WebGL off)
python tools/still.py --url http://127.0.0.1:8771/lab/
```

## Gates

`python tools/gates.py --serve .output/public` runs G1 (fps over a 15 s scripted scroll at 1280x800, pass 55+),
G2 (first-load bytes, pass 8 MB or less) and G3 (scroll moves the object, hover flips the cursor, ES/EN swaps
every string, WebGL off shows the still). Probe state lives in `document.documentElement.dataset.lab`.
