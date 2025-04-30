<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useWebSocket } from '../websocket' // shared websocket

const props = defineProps({
  streamid: String,
})

const loading = ref(true) 
const status = ref('UNKNOWN')

const socket = useWebSocket() // use the shared socket

const statusColor = computed(() => {
  switch (status.value) {
    case 'OK': return 'status-ok'
    case 'UNKNOWN': return 'status-unknown'
    case 'TIMEOUT':
    case 'NO_STREAM': return 'status-timeout'
    case 'NO_CONNECTION':
    case 'ERROR': return 'status-no_connection'
    default: return 'status-unknown'
  }
})

async function fetchStreamStatus() {
  try {
    const response = await fetch('/streams/' + props.streamid)
    if (response.ok) {
      const data = await response.json()
      status.value = data.status || 'UNKNOWN'
    } else {
      console.error('Failed to fetch streams:', response.status)
    }
  } catch (error) {
    console.error('Error fetching streams:', error)
  }
}

function handleLoad() {
  loading.value = false
}

function handleError() {
  loading.value = false
  console.error('Thumbnail failed to load.')
}

function handleMessage(event) {
  const data = JSON.parse(event.data)
  if (data.type !== 'stream/status_update') return
  if (data.stream_id == props.streamid) {
    console.log(props.streamid,'- Received message:', data)
    status.value = data.status
  }
}

onMounted(() => {
  fetchStreamStatus()

  if (socket.value) {
    socket.value.addEventListener('message', handleMessage)
  }
})

onBeforeUnmount(() => {
  if (socket.value) {
    socket.value.removeEventListener('message', handleMessage)
  }
})
</script>


<template>
  <div id="streamPreview">
    <img
      :src="'/thumbnail/' + streamid"
      class="previewImage"
      @load="handleLoad"
      @error="handleError"
    />
    <div v-if="loading" class="spinner"></div> 
    <div class="previewFooter">
      <div :class="['previewStatusIndicator', statusColor]"></div>
      <p class="previewText">{{ streamid }}</p>
    </div>
  </div>
</template>


<style scoped>
#streamPreview {
  width: 233px;
  height: 162px;
  background-color: #23252C;
  flex-shrink: 0;
  border-radius: 15px;
  overflow: hidden;
  position: relative; 
  border: #23252C solid 1px;
}

.previewImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 15px;
  position: absolute;
  top: 0;
  left: 0;
}

.spinner {
  position: absolute;
  top: calc( 50% - 18.5px );
  left: 50%;
  width: 30px;
  height: 30px;
  margin: -15px 0 0 -15px;
  border: 4px solid #4a4d57;
  border-top: 4px solid #40F284;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.previewFooter {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 37px;
  background-color: #23252C;
  display: flex;
  align-items: center;
}

.previewStatusIndicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: 13px;
  background-color: #4a4d57; /* default */
}

.status-ok {
  background-color: #40F284;
}

.status-unknown {
  background-color: #4a4d57;
}

.status-timeout,
.status-no_stream {
  background-color: #f2b440;
}

.status-no_connection,
.status-error {
  background-color: #f25540;
}


.previewText {
  font-weight: 700;
  font-size: 1rem;
  margin-left: 13px;
  margin-top: 18px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  width: calc(100% - 54px);
}
</style>
