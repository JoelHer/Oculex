<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useWebSocket } from '../websocket' // shared websocket
import { Icon } from '@iconify/vue'

const props = defineProps({
  streamid: String,
  preview: {
    type: Boolean,
    default: false
  },
  previewStreamSource: {
    type: String,
    default: '/data/rtsp.png'
  },
  editMode: {
    type: Boolean,
    default: false
  }
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

watch(() => props.previewStreamSource, (newVal, oldVal) => {
  fallbackTriggered.value = false
  loading.value = true
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

const fallbackUrl = '/static/www/compiled/vite.svg'
const afterUrl = ref('')

function handleError() {
  loading.value = false
  fallbackTriggered.value = true
}

const fallbackTriggered = ref(false)


function handleMessage(event) {
  const data = JSON.parse(event.data)
  if (data.type == 'stream/status_update'){
    if (data.stream_id == props.streamid) {
      console.log(props.streamid,'- Received message:', data)
      status.value = data.status
    }
  } else if (data.type == "stream/thumbnail_update") {
    if (data.stream_id == props.streamid) {
      console.log(props.streamid,'- Received message:', data)
      status.value = data.status
      afterUrl.value = "?"+Date.now()
    }
  }
}

onMounted(() => {
  if (props.preview) {
    console.log('Preview mode enabled for stream:', props.streamid)
    loading.value = false
    status.value = 'NO_STREAM'
  } else {
    fetchStreamStatus()
  }

  if (socket.value) {
    socket.value.addEventListener('message', handleMessage)
  }

})

onBeforeUnmount(() => {
  if (socket.value) {
    socket.value.removeEventListener('message', handleMessage)
  }
})


const imageUrl = computed(() => {
  if (fallbackTriggered.value) {
    return fallbackUrl
  }
  if (props.preview) {
    return '/preview/' + btoa(props.previewStreamSource) + afterUrl.value
  } else {
    return '/thumbnail/' + props.streamid + afterUrl.value
  }
})

</script>


<template>
  <div id="streamPreview">
    <template v-if="!fallbackTriggered">
      <img 
        :src="imageUrl"
        class="previewImage"
        :style="{ filter: editMode ? 'blur(4px)' : 'blur(0px)', transition: 'filter 0.3s ease' }"
        @load="handleLoad"
        @error="handleError"
      />
    </template>
    <template v-else>
      <div 
        class="fallbackIconContainer"
        :style="{ filter: editMode ? 'blur(4px)' : 'blur(0px)', transition: 'filter 0.3s ease' }"
      >
        <Icon icon="mdi:image-off" class="fallbackIcon" />
      </div>
    </template>
    <button v-if="editMode" class="editButton">
      <Icon icon="mdi-pen" style="font-size: 20px;" />
    </button>
    <button v-if="editMode" class="deleteButton">
      <Icon icon="mdi:trash-can-outline" style="font-size: 21px;" />
    </button>
    <div v-if="loading" class="spinner"></div> 
    <div class="previewFooter">
      <div :class="['previewStatusIndicator', statusColor]"></div>
      <p class="previewText">{{ streamid }}</p>
    </div>
  </div>
</template>


<style scoped>
.fallbackIconContainer {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #23252C;
}

.editButton {
  position: absolute;
  height: 37px;
  width: 37px;
  top: 10px;
  left: 10px;
  background-color: #406AF2;
  border: none;
  cursor: pointer;
  border-radius: 11px;
  padding: 0px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.deleteButton {
  position: absolute;
  height: 37px;
  width: 37px;
  top: 10px;
  right: 10px;
  background-color: #f25540;
  border: none;
  cursor: pointer;
  border-radius: 11px;
  padding: 0px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.fallbackIcon {
  font-size: 48px;
  color: #4a4d57;
}

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
