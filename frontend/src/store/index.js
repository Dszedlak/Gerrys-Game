import Vue from 'vue'
import Vuex from 'vuex'
import auth from './auth.module'

Vue.use(Vuex)

const store = new Vuex.Store({
  modules: {
    auth
  }
})

export default store;