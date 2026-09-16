<template>
  <canvas ref="canvas" class="gl" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'

// The 3D layer. One coral, four baked lighting passes cross-faded by scroll and pointer,
// one hotspot ring with spring physics. Reads useLabState() every frame, never the DOM.
const canvas = ref<HTMLCanvasElement | null>(null)
const state = useLabState()
const base = useRuntimeConfig().app.baseURL

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene, camera: THREE.PerspectiveCamera
let coral: THREE.Group, ring: THREE.Group, outerArc: THREE.Mesh, innerRing: THREE.Mesh
let material: THREE.ShaderMaterial
const clock = new THREE.Clock()
const blend = new THREE.Vector2(0.5, 0.65)
const camTarget = new THREE.Vector3(0, 0, 4.2)
const RING_R = 0.156
const ringScreen = { x: 0, y: 0, r: 0 }
let intro = 0
let rotY = -0.55
let spring = { inPr: 1, inVel: 0, outPr: 1, outVel: 0, lastKick: 0 }
let disposed = false

const VERT = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vNormal;
  void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`
const FRAG = /* glsl */ `
  uniform sampler2D uTL; uniform sampler2D uTR; uniform sampler2D uBL; uniform sampler2D uBR;
  uniform vec2 uBlend;
  uniform float uIntro;
  varying vec2 vUv;
  varying vec3 vNormal;
  void main() {
    vec3 top = mix(texture2D(uTL, vUv).rgb, texture2D(uTR, vUv).rgb, uBlend.x);
    vec3 bot = mix(texture2D(uBL, vUv).rgb, texture2D(uBR, vUv).rgb, uBlend.x);
    vec3 c = mix(bot, top, uBlend.y);
    float rim = pow(1.0 - abs(vNormal.z), 3.0);
    c += vec3(0.55, 0.42, 0.9) * rim * 0.16;
    c *= mix(0.15, 1.0, uIntro);
    gl_FragColor = vec4(c, 1.0);
    #include <colorspace_fragment>
  }
`

function softwareRenderer(gl: WebGLRenderingContext | WebGL2RenderingContext) {
  const dbg = gl.getExtension('WEBGL_debug_renderer_info')
  const name = dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : ''
  return /swiftshader|llvmpipe|software/i.test(name)
}

let mirrorTick = 0
function mirror() {
  // Probe surface for the gates. Written to a DOM attribute (not a window global) so a driver
  // evaluating in an isolated world can read it. Throttled to every 6th frame.
  if (state.ready && (mirrorTick++ % 6) !== 0) return
  const snap = {
    ready: state.ready, webgl: state.webgl, progress: +state.progress.toFixed(4), rotY: +rotY.toFixed(4),
    blend: { x: +blend.x.toFixed(3), y: +blend.y.toFixed(3) }, hover: state.hover,
    hotspotScreen: { x: Math.round(state.hotspotScreen.x), y: Math.round(state.hotspotScreen.y) },
    ringScreen: { x: Math.round(ringScreen.x), y: Math.round(ringScreen.y), r: Math.round(ringScreen.r) },
    lang: document.documentElement.lang
  }
  document.documentElement.dataset.lab = JSON.stringify(snap)
  ;(window as any).__lab = snap
}

function layout() {
  if (!renderer) return
  const w = window.innerWidth, h = window.innerHeight
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  const mobile = w < 760
  coral.position.x = mobile ? 0 : 0.85
  coral.position.y = mobile ? 0.35 : 0
  coral.scale.setScalar(mobile ? 0.8 : 1)
}

async function loadAssets() {
  const texLoader = new THREE.TextureLoader()
  const load = (n: string) => texLoader.loadAsync(`${base}textures/bake_${n}.webp`).then((t) => {
    t.colorSpace = THREE.SRGBColorSpace
    t.anisotropy = Math.min(4, renderer!.capabilities.getMaxAnisotropy())
    return t
  })
  const [tl, tr, bl, br] = await Promise.all([load('TL'), load('TR'), load('BL'), load('BR')])
  material = new THREE.ShaderMaterial({
    uniforms: {
      uTL: { value: tl }, uTR: { value: tr }, uBL: { value: bl }, uBR: { value: br },
      uBlend: { value: blend }, uIntro: { value: 0 }
    },
    vertexShader: VERT, fragmentShader: FRAG
  })
  const loader = new GLTFLoader()
  const draco = new DRACOLoader()
  draco.setDecoderPath(`${base}draco/`)
  draco.setDecoderConfig({ type: 'wasm' })
  loader.setDRACOLoader(draco)
  const gltf = await loader.loadAsync(`${base}models/coral.glb`)
  // The fan lies in its local XZ plane: tip it up so the face meets the camera (same pivot as the bake).
  const pivot = new THREE.Group()
  pivot.rotation.x = -Math.PI / 2
  pivot.add(gltf.scene)
  pivot.updateMatrixWorld(true)
  const box = new THREE.Box3().setFromObject(pivot)
  const size = new THREE.Vector3(); box.getSize(size)
  const centre = new THREE.Vector3(); box.getCenter(centre)
  const s = 2.1 / Math.max(size.x, size.y, size.z)
  const holder = new THREE.Group()
  holder.add(pivot)
  pivot.position.sub(centre)
  holder.scale.setScalar(s)
  gltf.scene.traverse((o: any) => {
    if (o.isMesh) { o.material = material; o.frustumCulled = false }
  })
  coral.add(holder)
}

function buildRing() {
  ring = new THREE.Group()
  const mat = (opacity: number) => new THREE.MeshBasicMaterial({ color: 0xd7afff, transparent: true, opacity, depthTest: false })
  innerRing = new THREE.Mesh(new THREE.RingGeometry(0.086, 0.1, 48), mat(0.95))
  outerArc = new THREE.Mesh(new THREE.RingGeometry(RING_R - 0.006, RING_R, 72, 1, 0, Math.PI * 1.55), mat(0.7))
  const dot = new THREE.Mesh(new THREE.CircleGeometry(0.018, 24), mat(1))
  innerRing.renderOrder = outerArc.renderOrder = dot.renderOrder = 10
  ring.add(innerRing, outerArc, dot)
  scene.add(ring)
}

function kick() {
  spring.inPr = 0; spring.outPr = 0
  spring.inVel = 0.2; spring.outVel = 0.2
  spring.lastKick = clock.elapsedTime
}

function tick() {
  if (disposed || !renderer) return
  const dt = Math.min(clock.getDelta(), 0.05)
  const t = clock.elapsedTime
  const p = state.progress
  const px = state.pointer.x, py = state.pointer.y

  intro = Math.min(1, intro + dt / 1.6)
  const easeIntro = 1 - Math.pow(1 - intro, 3)
  material.uniforms.uIntro.value = easeIntro

  // Scroll drives the turn; time adds a slow breath. One number in, everything follows.
  const targetRot = -0.55 + p * 1.1 + 0.06 * Math.sin(t * 0.5)
  rotY += (targetRot - rotY) * 0.08
  coral.rotation.y = rotY
  coral.rotation.z = 0.12 * Math.sin(p * Math.PI) + 0.02 * Math.sin(t * 0.7)
  const baseY = window.innerWidth < 760 ? 0.35 : 0
  coral.position.y = baseY + 0.12 - 0.35 * p + 0.03 * Math.sin(t * 0.7)
  const sc = (window.innerWidth < 760 ? 0.8 : 1) * (0.7 + 0.3 * easeIntro)
  coral.scale.setScalar(sc)

  // Light follows rotation and pointer: cross-fade between the four baked passes.
  const bx = THREE.MathUtils.clamp(0.5 + px * 0.35 + 0.35 * Math.sin(rotY), 0, 1)
  const by = THREE.MathUtils.clamp(0.65 + py * 0.3, 0, 1)
  blend.x += (bx - blend.x) * 0.08
  blend.y += (by - blend.y) * 0.08

  // Camera drifts toward the pointer.
  camTarget.set(px * 0.25, py * 0.18, 4.2)
  camera.position.lerp(camTarget, 0.04)
  camera.lookAt(0, 0, 0)

  // Hotspot ring: anchored beside the coral, always facing the camera.
  ring.position.set(coral.position.x + 0.42, coral.position.y + 0.38, 0.95)
  ring.quaternion.copy(camera.quaternion)
  outerArc.rotation.z = -t * 1.2
  spring.inVel = (1 - spring.inPr) * 0.015 + spring.inVel * 0.83
  spring.outVel = (1 - spring.outPr) * 0.008 + spring.outVel * 0.86
  spring.inPr += spring.inVel
  spring.outPr += spring.outVel
  innerRing.scale.setScalar(THREE.MathUtils.lerp(1, 1.25, spring.inPr))
  outerArc.scale.setScalar(THREE.MathUtils.lerp(1, 1.25, spring.outPr))
  if (!state.hover && t - spring.lastKick > 4) kick()

  // Hover test in screen space: the ring projected to pixels against the pointer.
  const v = ring.position.clone().project(camera)
  const w = window.innerWidth, h = window.innerHeight
  const sx = (v.x + 1) / 2 * w, sy = (1 - v.y) / 2 * h
  const dist = camera.position.distanceTo(ring.position)
  const rPx = RING_R * 1.25 * (h / 2) / (dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)))
  state.hotspotScreen.x = sx
  state.hotspotScreen.y = sy + rPx * 1.3 + 12
  ringScreen.x = sx; ringScreen.y = sy; ringScreen.r = rPx
  const mx = (px + 1) / 2 * w, my = (1 - py) / 2 * h
  const over = Math.hypot(mx - sx, my - sy) < rPx
  if (over !== state.hover) { state.hover = over; if (over) kick() }

  renderer.render(scene, camera)
  if (!state.ready) state.ready = true
  mirror()
}

// Breadcrumbs in the DOM: headless drivers cannot read the console, the DOM they can.
const crumb = (s: string) => { document.documentElement.dataset.scene = s }

onMounted(async () => {
  try {
    crumb('mounted')
    const probe = document.createElement('canvas')
    const gl = (probe.getContext('webgl2') || probe.getContext('webgl')) as WebGLRenderingContext | null
    if (!gl || softwareRenderer(gl)) {
      crumb('no-webgl')
      state.webgl = false; state.ready = true; mirror(); return
    }
    state.webgl = true
    renderer = new THREE.WebGLRenderer({ canvas: canvas.value!, antialias: true, alpha: true, powerPreference: 'high-performance' })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50)
    camera.position.copy(camTarget)
    coral = new THREE.Group()
    scene.add(coral)
    buildRing()
    layout()
    window.addEventListener('resize', layout)
    crumb('renderer')
    try {
      await loadAssets()
    } catch (e) {
      crumb('assets-failed: ' + String(e).slice(0, 200))
      state.webgl = false; state.ready = true; mirror(); return
    }
    crumb('assets')
    clock.start()
    kick()
    renderer.setAnimationLoop(tick)
  } catch (e) {
    crumb('error: ' + String(e).slice(0, 300))
    state.webgl = false; state.ready = true; mirror()
  }
})

onBeforeUnmount(() => {
  disposed = true
  window.removeEventListener('resize', layout)
  renderer?.setAnimationLoop(null)
  renderer?.dispose()
})
</script>
