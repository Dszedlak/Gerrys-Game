import Vue from "vue";
import VueRouter from "vue-router";

Vue.use(VueRouter);

const routes = [
  {
    path: '/rooms',
    name: 'Rooms',
    component: () => import('@/views/RoomList.vue')
  },
  {
    path: '/me',
    name: 'Profile',
    component: () => import('@/views/Profile.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/room',
    name: 'Room',
    component: () => import('@/views/Room.vue')
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  }
]

const router = new VueRouter({
  routes
});

export default router
