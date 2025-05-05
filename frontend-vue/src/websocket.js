import { ref } from 'vue'

const socket = ref(null)
const connectionStatus = ref('disconnected')

let reconnectTimeout = null
let connectionTimeout = null

function connect() {
  if (socket.value) return // already connecting or connected

  connectionStatus.value = 'connecting'

  try {
    const ws = new WebSocket(`ws://${window.location.host}/ws/streamstatus`)
    socket.value = ws

    // Set connection timeout (3 seconds)
    connectionTimeout = setTimeout(() => {
      console.warn('WebSocket connection timeout (3s)')
      if (socket.value === ws) {
        ws.close() // Triggers onclose
      }
    }, 3000)

    ws.onopen = () => {
      console.log('WebSocket connected')
      connectionStatus.value = 'connected'
      clearTimeout(connectionTimeout)
      clearTimeout(reconnectTimeout)
      connectionTimeout = null
      reconnectTimeout = null
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      cleanupAndReconnect()
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      ws.close() // Triggers onclose and reconnection
    }
  } catch (err) {
    console.error('WebSocket exception during connect():', err)
    cleanupAndReconnect()
  }
}

function cleanupAndReconnect() {
  connectionStatus.value = 'disconnected'

  if (socket.value) {
    try {
      socket.value.close()
    } catch (_) {}
  }

  socket.value = null

  clearTimeout(connectionTimeout)
  connectionTimeout = null

  if (!reconnectTimeout) {
    reconnectTimeout = setTimeout(() => {
      reconnectTimeout = null
      connect()
    }, 500) // fixed reconnect delay
  }
}

// Start automatically
connect()

export function useWebSocket() {
  return {
    socket,
    connectionStatus,
    reconnect: connect
  }
}
