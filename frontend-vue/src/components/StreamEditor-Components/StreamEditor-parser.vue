<script setup>
import { ref, onMounted, onUnmounted  } from 'vue'
import StreamEditorImageWithLoader from './StreamEditor-ImageWithLoader.vue'

import { EoesStream } from '../../models/EoesStream.js'

const now = ref(new Date())

let intervalId

onMounted(() => {
  intervalId = setInterval(() => {
    now.value = new Date() // triggers reactive updates
  }, 1000) // update every second
})

onUnmounted(() => {
  clearInterval(intervalId)
})


const brightness = ref(100)
const contrast = ref(-87)
const saturation = ref(0)
const rotation = ref(360)

const convertedStatus = ref('loading')
const parsedStatus = ref('loading')

const convertedTimestamp = ref(null)
const parsedTimestamp = ref(null)

const props = defineProps({
  stream: {
    type: EoesStream,
    required: true
  }
})

function onConvertedLoad() {
  convertedStatus.value = 'online'
  convertedTimestamp.value = new Date()
}

function onParsedLoad() {
  parsedStatus.value = 'online'
  parsedTimestamp.value = new Date()
}

function onImageError(type) {
  if (type === 'converted') convertedStatus.value = 'error'
  if (type === 'parsed') parsedStatus.value = 'error'
}

function timeAgo(ts) {
  if (!ts) return ''
  const diff = Math.floor((now.value.getTime() - ts.getTime()) / 1000)
  if (diff < 1) return 'just now'
  if (diff < 60) return `${diff}s ago`
  const mins = Math.floor(diff / 60)
  return `${mins}m ago`
}


</script>

<template>
  <div class="parser-settings">
    <h2 class="section-title">Parser Settings</h2>

    <div class="parser-grid">
      <div class="stream-box">
        <StreamEditorImageWithLoader 
          :streamUrl="`/snapshot/${encodeURIComponent(props.stream.name)}`"
          @load="onImageLoad"
          @error="onImageError"
          class="stream-img"
        />
        <div class="icon-bar">
          <button class="icon-btn">🔁</button>
          <button class="icon-btn">🖼️</button>
        </div>
        <div class="region-section">
          <span>Parse Regions</span>
          <select>
            <option>Box 1</option>
          </select>
          <div class="region-controls">
            <button class="icon-btn">➕</button>
            <button class="icon-btn danger">🗑️</button>
          </div>
        </div>
        <div class="image-settings">
          <label>Brightness</label>
          <input type="range" v-model="brightness" min="0" max="200" />

          <label>Contrast</label>
          <input type="range" v-model="contrast" min="-100" max="100" />

          <label>Saturation</label>
          <input type="range" v-model="saturation" min="-100" max="100" />

          <label>Rotation</label>
          <input type="range" v-model="rotation" min="0" max="360" />
        </div>
      </div>
      <div class="output-box">
        <div class="converted">
          <StreamEditorImageWithLoader 
            :streamUrl="`/snapshot/${encodeURIComponent(props.stream.name)}`"
            @load="onConvertedLoad"
            @error="() => onImageError('converted')"
            class="output-img"
          />
          <div class="status-line">
            <span>
              <span class="status-dot" :class="convertedStatus"></span>
              {{ convertedStatus === 'online' ? 'Successfully Converted' : 
                convertedStatus === 'error' ? 'Failed to Load Converted Image' : 
                'Loading Converted Image...' }}
            </span>
            <span class="timestamp">{{ timeAgo(convertedTimestamp) }}</span>
          </div>
        </div>

        <div class="parsed">
          <StreamEditorImageWithLoader 
            :streamUrl="`/computed/${encodeURIComponent(props.stream.name)}`"
            @load="onParsedLoad"
            @error="() => onImageError('parsed')"
            class="output-img"
          />
          <div class="status-line">
            <span>
              <span class="status-dot" :class="parsedStatus"></span>
              {{ parsedStatus === 'online' ? 'Successfully Parsed' : 
                parsedStatus === 'error' ? 'Failed to Parse Image' : 
                'Parsing Image...' }}
            </span>
            <span class="timestamp">{{ timeAgo(parsedTimestamp) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.parser-settings {
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

.parser-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.stream-box {
  background: #23252c;
  padding: 16px;
  border-radius: 15px;
  border: 2px solid #2d2f37;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.output-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.converted, .parsed {
  background: #23252c;
  padding: 12px;
  border-radius: 15px;
  border: 2px solid #2d2f37;
}

.stream-img, .output-img {
  width: 100%;
  border-radius: 8px;
}

.status-line {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  margin-top: 6px;
  color: #ccc;
}

.status.success {
  color: #00cc66;
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


.icon-bar {
  display: flex;
  gap: 10px;
}

.icon-btn {
  background: #333;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  color: white;
  cursor: pointer;
}

.icon-btn.danger {
  background: #aa3333;
}

.region-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.region-controls {
  display: flex;
  gap: 6px;
}

.image-settings {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

input[type="range"] {
  width: 100%;
}
</style>
