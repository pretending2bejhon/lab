import { shallowReactive } from 'vue'

// One shared state object for the page: the DOM (app.vue) writes scroll and pointer, the scene reads them
// every frame and writes back what the DOM needs (hover, hotspot screen position, ready flags).
// shallowReactive on purpose: pointer and hotspotScreen are plain objects mutated at 60 fps.
const state = shallowReactive({
  progress: 0,
  hover: false,
  cardOpen: false,
  ready: false,
  webgl: null as null | boolean,
  pointer: { x: 0, y: 0 },
  hotspotScreen: { x: 0, y: 0 }
})

export function useLabState() {
  return state
}
