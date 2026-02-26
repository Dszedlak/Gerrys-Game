// Production: Single origin (Flask serves everything)
// Development: Separate origins (localhost:8080 for frontend, localhost:5000 for backend)

const isDevelopment = process.env.NODE_ENV === 'development'

let IP_ADDRESS, BACKEND_PORT, BACKEND_PROTOCOL

if (isDevelopment) {
  // Development: read from .env.local (localhost or ngrok URLs)
  IP_ADDRESS = process.env.VUE_APP_BACKEND_IP || "localhost"
  BACKEND_PORT = process.env.VUE_APP_BACKEND_PORT || "5000"
  BACKEND_PROTOCOL = process.env.VUE_APP_BACKEND_PROTOCOL || "http"
} else {
  // Production: use current origin (Flask serves both frontend and backend)
  // This works for both localhost and any domain (including ngrok)
  IP_ADDRESS = window.location.hostname
  BACKEND_PORT = window.location.port || (window.location.protocol === 'https:' ? '443' : '80')
  BACKEND_PROTOCOL = window.location.protocol.replace(':', '')
}

// Use it to create API_URL and SOCKET_URL
export const API_URL = `${BACKEND_PROTOCOL}://${IP_ADDRESS}:${BACKEND_PORT}/api`
export const SOCKET_URL = `${BACKEND_PROTOCOL}://${IP_ADDRESS}:${BACKEND_PORT}`

export { IP_ADDRESS, BACKEND_PORT, BACKEND_PROTOCOL }
export default { API_URL, IP_ADDRESS, SOCKET_URL, BACKEND_PROTOCOL }