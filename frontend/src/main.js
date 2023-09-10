import Vue from "vue"
import App from '@/App.vue'
import router from '@/router'
import store from '@/store/index'
import ApiService from "@/services/ApiService"
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'

Vue.config.productionTip = false;
Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)

ApiService.init();

router.beforeEach((to, from, next) =>  {
  Promise.all([store.dispatch("checkAuth")]).then(next)
});

new Vue({
  router,
  store,
  render: (h) => h(App),
  data: {
    ipAddress: 'localhost',
  },
}).$mount('#app');