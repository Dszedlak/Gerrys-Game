/**
 * The "new version ready" banner: shown when the live build differs from the one this tab runs.
 */
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import UpdateBanner from '@/components/UpdateBanner.vue'

const flush = () => new Promise(resolve => jest.requireActual('timers').setImmediate(resolve))

function serveBuild(hash) {
  window.fetch = jest.fn(() => Promise.resolve({
    ok: true,
    text: () => Promise.resolve(`<html><script defer src="/js/app.${hash}.js"></script></html>`)
  }))
}

beforeEach(() => {
  jest.useFakeTimers()
  document.head.innerHTML = '<script src="http://localhost/js/app.aaaa1111.js"></script>'
})
afterEach(() => {
  jest.useRealTimers()
  document.head.innerHTML = ''
})

describe('UpdateBanner', () => {
  it('stays hidden while this tab runs the live version', async () => {
    serveBuild('aaaa1111')
    const wrapper = mount(UpdateBanner)
    jest.advanceTimersByTime(60 * 1000)
    await flush(); await nextTick()
    expect(window.fetch).toHaveBeenCalled()
    expect(wrapper.find('.update').exists()).toBe(false)
  })

  it('asks to refresh once a newer version is live', async () => {
    serveBuild('bbbb2222')
    const wrapper = mount(UpdateBanner)
    jest.advanceTimersByTime(60 * 1000)
    await flush(); await nextTick()
    expect(wrapper.find('.update').text()).toContain('new version')
    expect(window.fetch.mock.calls[0][1].headers['ngrok-skip-browser-warning']).toBe('1')
  })
})
