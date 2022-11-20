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
    path: '/me/quizzes',
    name: 'MyQuizzes',
    component: () => import('@/views/MyQuizzes.vue')
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
  }
]

const router = new VueRouter({
  routes
});

export default router
