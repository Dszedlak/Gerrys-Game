/**
 * In-game confirmation dialogs (instead of the browser's plain confirm box).
 *
 *   if (await askConfirm('Become a Pimp?')) ...
 *   await askConfirm('Discard “Knife”? It goes to the Black Market.', { danger: true, confirmText: 'Discard' })
 *
 * The question (up to the first "?") is the title; anything after it is the detail.
 * ConfirmHost.vue (mounted once in App.vue) shows them; without it (unit tests)
 * this falls back to window.confirm.
 */
let host = null

export function registerConfirmHost(fn) {
  host = fn
  return () => { if (host === fn) host = null }
}

const DANGER = /\b(discard|reset|restart|jail|stop|remove|end the game|leave)\b/i

export function askConfirm(message, options = {}) {
  const text = String(message || '')
  const cut = text.indexOf('?')
  const title = options.title || (cut !== -1 ? text.slice(0, cut + 1) : text)
  const detail = options.detail ?? (cut !== -1 ? text.slice(cut + 1).trim() : '')
  const request = {
    title,
    detail,
    confirmText: options.confirmText || 'Yes',
    cancelText: options.cancelText || 'Cancel',
    danger: options.danger ?? DANGER.test(title)
  }
  if (host) return host(request)
  return Promise.resolve(Boolean(window.confirm(text)))
}
