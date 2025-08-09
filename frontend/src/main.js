import { createApp } from 'vue'
import App from '@/App.vue'
import router from '@/router'
import store from '@/store/index'
import ApiService from "@/services/ApiService"
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'

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