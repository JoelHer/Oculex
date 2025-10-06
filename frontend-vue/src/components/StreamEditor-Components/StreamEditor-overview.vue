<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import StreamEditorImageWithLoader from './StreamEditor-ImageWithLoader.vue'

import { EoesStream } from '../../models/EoesStream.js'

// Dummy reactive values for now
const streamStatus = ref('Online')
const lastUpdated = ref('5s ago')

const props = defineProps({
  stream: {
    type: EoesStream,
    required: true
  }
})


const lastSnapshotUpdate = ref(null)
const lastComputedUpdate = ref(null)

const snapshotAgo = ref('—')
const computedAgo = ref('—')

const snapshotStatus = ref('loading') // 'online', 'error', 'loading'
const computedStatus = ref('loading')

let intervalId

function updateAgoLabels() {
  const now = Date.now()

  if (lastSnapshotUpdate.value) {
    const secs = Math.floor((now - lastSnapshotUpdate.value) / 1000)
    snapshotAgo.value = `${secs}s ago`
  }

  if (lastComputedUpdate.value) {
    const secs = Math.floor((now - lastComputedUpdate.value) / 1000)
    computedAgo.value = `${secs}s ago`
  }
}

function onSnapshotLoad() {
  lastSnapshotUpdate.value = Date.now()
  snapshotStatus.value = 'online'
}

function onSnapshotError() {
  snapshotStatus.value = 'error'
}

function onComputedLoad() {
  lastComputedUpdate.value = Date.now()
  computedStatus.value = 'online'
}

function onComputedError() {
  computedStatus.value = 'error'
}

onMounted(() => {
  intervalId = setInterval(updateAgoLabels, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<template>
  <div class="overview-view">
    <h2 class="section-title">Overview</h2>

    <div class="overview-grid">
      <div class="card">
        <StreamEditorImageWithLoader 
          :streamUrl="`/snapshotRaw/${encodeURIComponent(props.stream.name)}`"
          @load="onSnapshotLoad"
          @error="onSnapshotError"
          class="card-image"
        />

        <div class="card-footer">
          <span :class="['status-dot', snapshotStatus]"></span>
          <span>Live Snapshot • Updated {{ snapshotAgo }}</span>
        </div>
      </div>

      <div class="card">
        <StreamEditorImageWithLoader 
          :streamUrl="`/computed/${encodeURIComponent(props.stream.name)}`"
          @load="onComputedLoad"
          @error="onComputedError"
          class="card-image"
        />
        <div class="card-footer">
          <span :class="['status-dot', computedStatus]"></span>
          <span>Last OCR Input Img • {{ computedAgo }}</span>
        </div>
      </div>

      <div class="stream-box category-box">
        <h3 class="category-title">Stream Information</h3>
        <div class="category-body">
          <p><strong>Name:</strong> {{ props.stream.name }}</p>
          <p><strong>Snapshot Status:</strong> {{ snapshotStatus }}</p>
          <p><strong>Computed Status:</strong> {{ computedStatus }}</p>
          <p><strong>Snapshot Updated:</strong> {{ snapshotAgo }}</p>
          <p><strong>Computed Updated:</strong> {{ computedAgo }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-view {
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

.stream-box {
  background: #23252c;
  padding: 14px;
  border-radius: 15px;
  border: 2px solid #2d2f37;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.category-box { padding: 12px 14px; }
.category-title { color:#40F284; font-size:1.05rem; margin:0; font-weight:700; }
.category-body { display:flex; flex-direction:column; gap:10px; margin-top:6px; }

.category-box p {
  margin: 0px;
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
