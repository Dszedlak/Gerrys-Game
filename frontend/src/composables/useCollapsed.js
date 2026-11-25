import { ref, watch } from 'vue'

/**
 * A panel's collapsed / expanded state, remembered in this browser
 * (per viewer; it falls back to the default where storage is unavailable).
 */
export function useCollapsed(key, collapsedByDefault = false) {
  const storageKey = `gg.collapsed.${key}`
  let initial = collapsedByDefault
  try {
    const saved = window.localStorage.getItem(storageKey)
    if (saved !== null) initial = saved === '1'
  } catch (e) {
    // private window / blocked storage: just use the default
  }
  const collapsed = ref(initial)
  watch(collapsed, (v) => {
    try {
      window.localStorage.setItem(storageKey, v ? '1' : '0')
    } catch (e) {
      // ignore
    }
  })
  const toggle = () => { collapsed.value = !collapsed.value }
  return { collapsed, toggle }
}
