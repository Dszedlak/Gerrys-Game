import { ref, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import JwtService from '@/services/JwtService'
import { IP_ADDRESS } from "@/common/config"

export function useSocket() {
  const socket = io(`ws://${IP_ADDRESS}:5000/`, {
    transportOptions: {
      polling: {
        extraHeaders: {
          Authorization: `Bearer ${JwtService.getToken()}`
        }
      }
    }
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