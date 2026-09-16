<template>
  <div>
    <ClientOnly>
      <LabScene v-if="state.webgl !== false" />
    </ClientOnly>
    <div v-if="state.webgl === false" class="fallback">
      <img :src="base + 'coral-still.webp'" alt="" width="520" height="520" />
      <p data-i18n="fallback">{{ t('fallback') }}</p>
    </div>

    <header class="top">
      <a href="https://jhonalbert.com/" data-i18n="back">{{ t('back') }}</a>
      <button type="button" class="lang-btn" data-lang-btn :aria-label="t('langAria')" data-i18n="langBtn" @click="toggle">{{ t('langBtn') }}</button>
    </header>

    <div class="dom">
      <section class="hero">
        <div class="col">
          <p class="kicker">{{ t('kicker') }}</p>
          <h1 data-i18n="h1">{{ t('h1') }}</h1>
          <p class="lead" data-i18n="sub1">{{ t('sub1') }}</p>
          <p class="lead strong" data-i18n="sub2">{{ t('sub2') }}</p>
          <p class="hint" data-i18n="scroll">{{ t('scroll') }}</p>
        </div>
      </section>
      <section class="spacer" aria-hidden="true"></section>
      <section class="spacer" aria-hidden="true"></section>
      <section class="end">
        <div class="col">
          <p class="foot reveal" data-i18n="footer">{{ t('footer') }}</p>
          <a class="reveal" href="https://jhonalbert.com/" data-i18n="back">{{ t('back') }}</a>
          <p class="meta reveal" data-i18n="specimen">{{ t('specimen') }}</p>
        </div>
      </section>
    </div>

    <span ref="label" class="hotspot-label" :class="{ on: state.ready && state.webgl }" data-i18n="hotspot">{{ t('hotspot') }}</span>

    <div v-if="state.cardOpen" class="card" role="dialog">
      <h2 data-i18n="cardTitle">{{ t('cardTitle') }}</h2>
      <p data-i18n="cardLine">{{ t('cardLine') }}</p>
      <button type="button" data-i18n="cardClose" @click="state.cardOpen = false">{{ t('cardClose') }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'

const { t, toggle, restore } = useLang()
const state = useLabState()
const base = useRuntimeConfig().app.baseURL
const label = ref<HTMLElement | null>(null)

useHead({ title: 'Lab · Coral' })

onMounted(() => {
  // Error trap into the DOM (headless drivers cannot read the console).
  window.addEventListener('error', (e) => { document.documentElement.dataset.err = String(e.message).slice(0, 300) })
  window.addEventListener('unhandledrejection', (e: PromiseRejectionEvent) => { document.documentElement.dataset.err = 'rejection: ' + String(e.reason).slice(0, 300) })
  restore()
  gsap.registerPlugin(ScrollTrigger)

  // Lenis owns the scroll, GSAP owns time; one progress number leaves here for the scene.
  const lenis = new Lenis({ lerp: 0.1, smoothWheel: true })
  lenis.on('scroll', ScrollTrigger.update)
  gsap.ticker.add((time) => lenis.raf(time * 1000))
  gsap.ticker.lagSmoothing(0)
  ScrollTrigger.create({
    trigger: document.body, start: 'top top', end: 'bottom bottom',
    onUpdate: (self) => { state.progress = self.progress }
  })
  gsap.utils.toArray<HTMLElement>('.reveal').forEach((el) => {
    gsap.to(el, { opacity: 1, y: 0, duration: 1.1, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } })
  })

  const onMove = (e: PointerEvent) => {
    state.pointer.x = (e.clientX / window.innerWidth) * 2 - 1
    state.pointer.y = -((e.clientY / window.innerHeight) * 2 - 1)
  }
  window.addEventListener('pointermove', onMove, { passive: true })
  window.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch') onMove(e)
  }, { passive: true })
  window.addEventListener('click', (e) => {
    const el = e.target as HTMLElement
    if (el.closest('a, button, .card')) return
    if (state.hover) state.cardOpen = !state.cardOpen
  })
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') state.cardOpen = false })

  // The hotspot label follows the ring; written straight to style, no re-render per frame.
  gsap.ticker.add(() => {
    if (label.value) label.value.style.transform = `translate(${state.hotspotScreen.x - label.value.offsetWidth / 2}px, ${state.hotspotScreen.y}px)`
  })
})

watch(() => state.hover, (h) => {
  if (h) document.body.dataset.cursor = 'pointer'
  else delete document.body.dataset.cursor
})
</script>

<style>
@import "~/assets/css/main.css";
</style>
