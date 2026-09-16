// Two-language dictionary. ES is the source, EN the twin. Every visible string goes through t().
export type Lang = 'es' | 'en'

const DICT: Record<string, { es: string; en: string }> = {
  kicker: { es: 'LAB · CORAL', en: 'LAB · CORAL' },
  h1: { es: 'Un coral que responde al scroll.', en: 'A coral that answers the scroll.' },
  sub1: {
    es: 'Prueba de una capa 3D para páginas que se sienten vivas. Luz horneada, nada corre en un servidor.',
    en: 'A test of a 3D layer for pages that feel alive. Baked light, nothing runs on a server.'
  },
  sub2: {
    es: 'El movimiento es la capa. La palabra sigue siendo el trabajo.',
    en: 'The motion is the layer. The words are still the work.'
  },
  scroll: { es: 'DESPLAZA', en: 'SCROLL' },
  hotspot: { es: 'Tocar el coral', en: 'Touch the coral' },
  cardTitle: { es: 'Coral, ejemplar de acceso abierto', en: 'Coral, an open-access specimen' },
  cardLine: {
    es: 'Pases de luz horneados y cruzados por la rotación. Tu máquina no calcula nada pesado.',
    en: 'Baked light passes crossed by the rotation. Your machine does no heavy lifting.'
  },
  cardClose: { es: 'Cerrar', en: 'Close' },
  fallback: { es: 'Tu navegador no muestra 3D. Aquí va la imagen fija.', en: 'Your browser does not show 3D. Here is the still.' },
  back: { es: 'Volver a jhonalbert.com', en: 'Back to jhonalbert.com' },
  footer: {
    es: 'Una página puede sentirse viva y aun así pedir una sola cosa. Esa parte la escribo yo.',
    en: 'A page can feel alive and still ask for one thing. That part I write.'
  },
  langBtn: { es: 'EN', en: 'ES' },
  langAria: { es: 'Switch to English', en: 'Cambiar a español' },
  specimen: { es: 'Ejemplar: Corallium sp., Smithsonian NMNH, dominio público', en: 'Specimen: Corallium sp., Smithsonian NMNH, public domain' }
}

export function useLang() {
  const lang = useState<Lang>('lang', () => 'es')
  const t = (key: string) => {
    const e = DICT[key]
    if (!e) return key
    return e[lang.value]
  }
  const toggle = () => {
    lang.value = lang.value === 'es' ? 'en' : 'es'
    apply()
  }
  const apply = () => {
    if (!import.meta.client) return
    document.documentElement.lang = lang.value
    try { localStorage.setItem('lab-lang', lang.value) } catch {}
    if ((window as any).__lab) (window as any).__lab.lang = lang.value
  }
  const restore = () => {
    if (!import.meta.client) return
    try {
      const saved = localStorage.getItem('lab-lang')
      if (saved === 'en' || saved === 'es') lang.value = saved
    } catch {}
    apply()
  }
  return { lang, t, toggle, restore }
}
