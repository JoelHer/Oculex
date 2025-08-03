<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import StreamEditorImageWithLoader from './StreamEditor-ImageWithLoader.vue'

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
const ocrEngine = ref('Tesseract') // Dummy for now

let intervalId

function updateAgoLabels() {
  const now = Date.now()
  if (lastParseUpdate.value) {
    const secs = Math.floor((now - lastParseUpdate.value) / 1000)
    parseAgo.value = `${secs}s ago`
  }
}

function onParseImageLoad() {
  lastParseUpdate.value = Date.now()
  ocrStatus.value = 'online'
  parsedText.value = '123456.78' // Simulated result
  confidence.value = 93.2
}

function onParseImageError() {
  ocrStatus.value = 'error'
}

onMounted(() => {
  intervalId = setInterval(updateAgoLabels, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <div class="ocr-view">
    <h2 class="section-title">OCR</h2>

    <div class="overview-grid">
      <div class="card">
        <StreamEditorImageWithLoader 
          :streamUrl="`/parsed/${encodeURIComponent(props.stream.name)}`"
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
