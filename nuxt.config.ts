// Lab: 3D layer tests for jhonalbert.com. Static export served at jhonalbert.com/lab/.
export default defineNuxtConfig({
  ssr: true,
  compatibilityDate: '2026-09-16',
  devtools: { enabled: false },
  telemetry: false,
  app: {
    baseURL: '/lab/',
    head: {
      htmlAttrs: { lang: 'es' },
      title: 'Lab · Coral',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Un coral que responde al scroll. Prueba de una capa 3D para páginas que se sienten vivas.' },
        { name: 'theme-color', content: '#030209' },
        { name: 'robots', content: 'noindex' }
      ]
    }
  },
  nitro: { prerender: { crawlLinks: false, routes: ['/'] } },
  vite: { build: { target: 'es2022' } }
})
