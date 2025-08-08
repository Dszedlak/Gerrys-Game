import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Rooms from '@/views/RoomList.vue'
import Profile from '@/views/Profile.vue'
import Login from '@/views/Login.vue'
import Room from '@/views/Room.vue'

const routes = [
  { path: '/rooms', name: 'Rooms', component: Rooms },
  { path: '/me', name: 'Profile', component: Profile },
  { path: '/login', name: 'Login', component: Login },
  { path: '/room', name: 'Room', component: Room },
  { path: '/home', name: 'Home', component: Home },
  { path: '/', redirect: '/home' } // <-- Add this line
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
