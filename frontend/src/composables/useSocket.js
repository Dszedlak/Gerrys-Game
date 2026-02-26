import { ref, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import JwtService from '@/services/JwtService'
import { SOCKET_URL } from "@/common/config"

export function useSocket() {
  const token = JwtService.getToken()
  const socket = io(SOCKET_URL, {
    // Force polling so Authorization header is sent by the browser
    transports: ['polling'],
    transportOptions: {
      polling: {
        extraHeaders: {
          Authorization: `Bearer ${token}`
        }
      }
    },
    // Also pass token via auth for future server support
    auth: { token }
  })

  const isConnected = ref(false)

  socket.on('connect', () => {
    isConnected.value = true
    // Example: emit join event on connect
    socket.emit('join')
  })
  socket.on('disconnect', () => {
    isConnected.value = false
  })

  onUnmounted(() => {
    socket.disconnect()
  })

  return { socket, isConnected }
}