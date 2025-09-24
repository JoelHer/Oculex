<script setup>
import { ref, onMounted, onUnmounted, watch, emit } from 'vue'
import StreamEditorImageWithLoader from './StreamEditor-ImageWithLoader.vue'
import ColorPicker from '../ColorPicker.vue'
import { useWebSocket } from '../../websocket'

import { EoesStream } from '../../models/EoesStream.js'

const props = defineProps({
  stream: {
    type: EoesStream,
    required: true
  }
})

const lastParseUpdate = ref(null)
const parseAgo = ref('—')
const ocrStatus = ref('loading')
const parsedText = ref('—')
const confidence = ref(null)
const ocrEngine = ref('not fetched') // Dummy for now

const ocrRunning = ref(false)

const imageRevision = ref(null) // Used for cache busting
const isSaving = ref(false)
const selectedColor = ref('#00ffff')
let oSelectedColor = selectedColor.value

const isCleanForm = ref(true)

const { socket, connectionStatus, reconnect } = useWebSocket()

watch(selectedColor, (nV, oV)=>{
  if (nV != oSelectedColor) {
    isCleanForm.value = false
  }
  if (nV == oSelectedColor) {
    isCleanForm.value = true
  }
})

let intervalId

function updateAgoLabels() {
  const now = Date.now()
  if (lastParseUpdate.value) {
    const secs = Math.floor((now - lastParseUpdate.value) / 1000)
    parseAgo.value = `${secs}s ago`
  }
}

function onParseImageLoad() {  
  fetch(`/streams/${props.stream.name}/ocr?t=${Date.now()}`)
  .then(response => response.json())
  .then(data => {
      if (data.results.aggregate) {
        ocrStatus.value = 'online'
        parsedText.value = data.results.aggregate.value || null
        confidence.value = data.results.aggregate.confidence*100 || null
        lastParseUpdate.value =  data.results.aggregate.timestamp*1000 || null
      } else {

        if (data.results) {
          stringedText = ''
          totalConfidence = 0
          data.results.forEach(res => {
            stringedText += res.text || ''
            totalConfidence += (res.confidence || 0) * 100
          });
          confidence.value = totalConfidence / data.results.length || null
          parsedText.value = stringedText || null
          lastParseUpdate.value = Date.now()
          ocrStatus.value = 'online'
        }
      }
    })
    .catch(error => {
      console.error('Error fetching OCR settings:', error)
    })
}

function onParseImageError() {
  ocrStatus.value = 'error'
}

function handleMessage(event) {
  const data = JSON.parse(event.data)
  if (data.type == 'stream/ocr_status') {
    if (data.stream_id == props.streamid) {
      ocrStatus.value = data.ocr_running ? 'Running' : 'nothing'
      ocrRunning.value = data.ocr_running
    }
  }
}

onMounted(() => {
  intervalId = setInterval(updateAgoLabels, 1000)
  imageRevision.value = Date.now() // Initialize to bust cache
  fetch(`/streams/${props.stream.name}/ocr-settings`)
    .then(response => response.json())
    .then(data => {
      ocrEngine.value = data.ocr_engine || 'EasyOCR'
      selectedColor.value = data.ocr_color || '#000000'
      oSelectedColor = selectedColor.value
    })
    .catch(error => {
      console.error('Error fetching OCR settings:', error)
    })

  fetch(`/streams/${props.stream.name}?t=${Date.now()}`)
    .then(response => response.json())
    .then(data => {
      ocrRunning.value = data.ocrRunning
      console.log("Fetched initial OCR running state:", ocrRunning.value)
    })
    .catch(error => {
      console.error('Error fetching stream status:', error)
    })

  if (socket.value) {
    const handler = (event) => {
      handleMessage(event) // your function
    }
    socket.value.addEventListener('message', handler)

    onUnmounted(() => {
      socket.value.removeEventListener('message', handler)
    })
  }
})

onUnmounted(() => {
  clearInterval(intervalId)
})

async function saveOCRSettings() {
  isSaving.value = true
  try {
    const response = await fetch(`/streams/${props.stream.name}/ocr-settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ocr_engine: "EasyOCR",
        ocr_color: selectedColor.value
      })
    })

    if (!response.ok) {
      throw new Error('Failed to save changes')
    } else {
      // Update the stream object with new values so the isDirty computed property updates
      //props.stream.url = editedRtspUrl.value
      //props.stream.name = editedName.value
      oSelectedColor = selectedColor.value
      isCleanForm.value = true
    }
  } catch (error) {
    console.error('Error saving changes:', error)
  } finally {
    isSaving.value = false
  }
}

</script>

<template>
  <div class="ocr-view">
    <h2 class="section-title">OCR</h2>

    <div class="overview-grid">
      <div class="card">
        <div class="card-body">
          <h3>OCR Settings</h3>
          <p><strong>OCR Engine:</strong> {{ ocrEngine }}</p>
          <p><strong>Highlight Color: </strong><ColorPicker v-model="selectedColor"/></p>
          <button @click="saveOCRSettings" :disabled="isCleanForm || isSaving">Save Settings</button>
        </div>
      </div>
      <div class="card">
        <StreamEditorImageWithLoader 
          :streamUrl="`/streams/${encodeURIComponent(props.stream.name)}/ocr-withimage?t=${imageRevision}`"
          @load="onParseImageLoad"
          @error="onParseImageError"
          class="card-image"
        />

        <div class="card-footer">
          <span :class="['status-dot', ocrStatus]"></span>
          <span>Parsed OCR Image • {{ parseAgo }}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <h3>OCR Output</h3>
          <p><strong>Parsed Text:</strong> {{ parsedText }}</p>
          <p><strong>Confidence:</strong> {{ confidence !== null ? confidence.toFixed(1) + '%' : '—' }}</p>
          <p><strong>Engine:</strong> {{ ocrEngine }}</p>
          <p><strong>Status:</strong> {{ ocrStatus }}</p>
          <p><strong>Last Updated:</strong> {{ parseAgo }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ocr-view {
  display: flex;
  flex-direction: column;
  gap: 15px;
  color: white;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 5px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.card {
  background: #23252c;
  border: 2px solid #2d2f37;
  border-radius: 15px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-image {
  width: 100%;
  height: auto;
  object-fit: cover;
  border-bottom: 1px solid #2d2f37;
}

.card-footer {
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #ccc;
}

.card-body {
  padding: 16px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
  display: inline-block;
  background-color: #4a4d57; 
}

.status-dot.online {
  background-color: #40F284;
}

.status-dot.error {
  background-color: #f25540;
}

.status-dot.loading {
  background-color: #4a4d57;
}
</style>
