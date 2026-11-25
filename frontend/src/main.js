import { createApp } from 'vue'
import App from '@/App.vue'
import router from '@/router'
import store from '@/store/index'
import ApiService from "@/services/ApiService"
import axios from 'axios'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'
import '@fontsource/barlow-condensed'
import '@/styles/overrides.css'

import { BNavbar, BNavbarBrand, BNavbarNav, BNavItem, BCollapse, BModal, BButton, BContainer, BRow, modalManagerPlugin } from 'bootstrap-vue-next'

ApiService.init();

// Restore Vuex auth state from localStorage
const token = localStorage.getItem('token');
const username = localStorage.getItem('username');
if (token && username) {
  store.commit('auth/setUser', { username, token });
}

if (token) {
  ApiService.setHeader(token)
}

// Any request the server refuses as "not signed in" means our saved sign-in
// is stale (expired, or the server was reset): sign out and go to the login page.
axios.interceptors.response.use(
  response => response,
  error => {
    const status = error?.response?.status
    const url = error?.config?.url || ''
    const isAuthCall = /auth\/(login|register|verify-token)/.test(url)
    if (status === 401 && !isAuthCall && store.state.auth.token) {
      store.commit('auth/expireSession')
      if (router.currentRoute.value.name !== 'Login') router.push({ name: 'Login' })
    }
    return Promise.reject(error)
  }
)

// Check the saved sign-in now, rather than trusting what's in localStorage
if (token) {
  store.dispatch('auth/checkAuth').then((ok) => {
    if (!ok && router.currentRoute.value.name !== 'Login') router.push({ name: 'Login' })
  })
}

const app = createApp(App)
app.use(router)
app.use(store)
app.use(modalManagerPlugin)

app.component('BNavbar', BNavbar)
app.component('BNavbarBrand', BNavbarBrand)
app.component('BNavbarNav', BNavbarNav)
app.component('BNavItem', BNavItem)
app.component('BCollapse', BCollapse)
app.component('BModal', BModal)
app.component('BButton', BButton)
app.component('BContainer', BContainer)
app.component('BRow', BRow)

app.mount('#app')