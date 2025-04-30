// websocket.js
import { ref } from 'vue'

const socket = ref(null)
let reconnectTimeout = null

export function useWebSocket() {
  function connect() {
    socket.value = new WebSocket(`ws://${window.location.host}/ws/streamstatus`)

    socket.value.onopen = () => {
      console.log('WebSocket connected')
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
        reconnectTimeout = null
      }
    }

    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    socket.value.onclose = () => {
      console.log('WebSocket closed')
      socket.value = null
      if (!reconnectTimeout) {
        reconnectTimeout = setTimeout(() => {
          console.log('Trying to reconnect WebSocket...')
          connect()
        }, 500)
      }
    }
  }

  if (!socket.value) {
    connect()
  }

  return socket
}
