<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
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

// --- reactive ---
const lastParseUpdate = ref(null)
const parseAgo = ref('—')
const ocrStatus = ref('loading')
const parsedText = ref('—')
const confidence = ref(null)
const ocrEngine = ref('not fetched')
const ocrEngineOptions = ref([]) // dropdown options

const ocrRunning = ref(false)

const imageRevision = ref(null) // cache busting
const isSaving = ref(false)
const ocrTriggering = ref(false) // new: Run OCR busy state
const selectedColor = ref('#00ffff')
let oSelectedColor = selectedColor.value

const isCleanForm = ref(true)

const { socket, connectionStatus, reconnect } = useWebSocket()

watch(selectedColor, (nV) => {
  isCleanForm.value = (nV === oSelectedColor)
})

let intervalId

function updateAgoLabels() {
  const now = Date.now()
  if (lastParseUpdate.value) {
    const secs = Math.floor((now - lastParseUpdate.value) / 1000)
    parseAgo.value = `${secs}s ago`
  } else {
    parseAgo.value = '—'
  }
}

/**
 * Fetch OCR results and update local state.
 * Returns the fetch promise so callers (runOCR) can await if desired.
 */
function onParseImageLoad() {
  return fetch(`/streams/${props.stream.name}/ocr?t=${Date.now()}`)
    .then(response => response.json())
    .then(data => {
      lastParseUpdate.value =  data.timestamp * 1000
      if (data.results && data.results.aggregate) {
        ocrStatus.value = 'online'
        parsedText.value = data.results.aggregate.value || '—'
        confidence.value = (data.results.aggregate.confidence != null) ? (data.results.aggregate.confidence * 100) : null
        lastParseUpdate.value = (data.results.aggregate.timestamp) ? data.results.aggregate.timestamp * 1000 : 0
        return
      }

      if (data.results && Array.isArray(data.results)) {
        // collect and sanitize pieces
        const texts = data.results.map(r => (r.text || '').replace(/\r/g, '').trim())

        // compute average length to detect "one-character-per-line" cases
        const totalLen = texts.reduce((s, t) => s + (t ? t.length : 0), 0)
        const avgLen = texts.length ? (totalLen / texts.length) : 0

        let combined = ''
        if (avgLen > 1.5 || texts.length <= 4) {
          // normal case: join with spaces, keep readability (avoid forced newlines per char)
          combined = texts.filter(Boolean).join(' ')
        } else {
          // likely single-char-per-entry (e.g. characters split vertically) -> join without separators
          combined = texts.join('')
        }

        parsedText.value = combined.trim() || '—'

        // confidence: average of confidences if available
        let confSum = 0, confCount = 0
        data.results.forEach(r => {
          if (r.confidence != null) {
            confSum += (r.confidence || 0) * 100
            confCount++
          }
        })
        confidence.value = confCount ? (confSum / confCount) : null

        
        
        ocrStatus.value = 'online'
        return
      }
      
      // fallback
      parsedText.value = '—'
      confidence.value = null
      ocrStatus.value = 'online'
    })
    .catch(error => {
      console.error('Error fetching OCR results:', error)
      ocrStatus.value = 'error'
    })
}

function onParseImageError() {
  ocrStatus.value = 'error'
}

function handleMessage(event) {
  try {
    const data = JSON.parse(event.data)
    if (data.type === 'stream/ocr_status' && data.stream_id === props.stream.name) {
      ocrStatus.value = data.ocr_running ? 'online' : 'nothing'
      ocrRunning.value = !!data.ocr_running
      
      console.log('Received OCR status message:', data)

      if (data.data) {
        console.log('Received OCR data message:', data.data)
        lastParseUpdate.value = data.data.timestamp * 1000
        updateAgoLabels()
        imageRevision.value = Date.now() // bust cache
      }
    }
  } catch (e) {
    // ignore non-json or unexpected messages
  }
}

onMounted(() => {
  intervalId = setInterval(updateAgoLabels, 1000)
  imageRevision.value = Date.now()

  fetch(`/streams/${props.stream.name}/ocr-settings`)
    .then(response => response.json())
    .then(data => {
      ocrEngine.value = data.ocr_engine || 'EasyOCR'
      if (Array.isArray(data.available_engines) && data.available_engines.length) {
        ocrEngineOptions.value = data.available_engines
      } else {
        ocrEngineOptions.value = [ocrEngine.value]
      }
      selectedColor.value = data.ocr_color || '#00ffff'
      oSelectedColor = selectedColor.value
    })
    .catch(error => {
      console.error('Error fetching OCR settings:', error)
      ocrEngineOptions.value = ['EasyOCR']
      ocrEngine.value = 'EasyOCR'
    })

  fetch(`/streams/${props.stream.name}?t=${Date.now()}`)
    .then(response => response.json())
    .then(data => {
      ocrRunning.value = !!data.ocrRunning
    })
    .catch(error => {
      console.error('Error fetching stream status:', error)
    })

  if (socket.value) {
    const handler = (event) => handleMessage(event)
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ocr_engine: ocrEngine.value,
        ocr_color: selectedColor.value
      })
    })

    if (!response.ok) throw new Error('Failed to save')
    oSelectedColor = selectedColor.value
    isCleanForm.value = true
  } catch (error) {
    console.error('Error saving changes:', error)
    alert('Fehler beim Speichern der OCR-Einstellungen')
  } finally {
    isSaving.value = false
  }
}

async function runOCR() {
  if (ocrTriggering.value) return
  ocrTriggering.value = true
  ocrStatus.value = 'loading'
  try {
    const res = await fetch(`/streams/${props.stream.name}/ocr/run`, {
      method: 'POST'
    })
    if (!res.ok) {
      const txt = await res.text().catch(()=>null)
      throw new Error(txt || res.statusText || 'Trigger failed')
    }

    imageRevision.value = Date.now()
    lastParseUpdate.value = Date.now()
    await onParseImageLoad()
  } catch (err) {
    console.error('Error triggering OCR run:', err)
    alert('Fehler beim Starten der OCR: ' + (err.message || 'unknown'))
  } finally {
    ocrTriggering.value = false
  }
}
</script>

<template>
  <div class="ocr-root">
    <h2 class="section-title">OCR</h2>

    <div class="ocr-layout">
      <div class="left-col">
        <div class="stream-box category-box">
          <h3 class="category-title">Parsed OCR Image</h3>
          <div class="category-body">
            <div class="image-wrapper">
              <StreamEditorImageWithLoader
                :streamUrl="`/streams/${encodeURIComponent(props.stream.name)}/ocr-withimage?t=${imageRevision}`"
                @load="onParseImageLoad"
                @error="onParseImageError"
                class="parsed-image"
              />
            </div>
            <div class="form-field readonly">
              <div class="output-meta">
                <div class="output-chip">
                  <div class="chip-label">Status</div>
                  <div style="display:flex;gap:8px;align-items:center;">
                    <span :class="['status-dot', ocrStatus]"></span>
                    <div class="chip-value">{{ ocrStatus === 'loading' ? 'Loading…' : (parseAgo || '—') }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="stream-box category-box">
          <h3 class="category-title">OCR Output</h3>
          <div class="category-body">
            <div class="output-meta">
              <div class="output-chip">
                <div class="chip-label">Confidence</div>
                <div class="chip-value">
                  <div v-if="ocrStatus === 'loading'" class="skeleton skeleton-text"></div>
                  <template v-else>
                    {{ confidence !== null ? (confidence.toFixed(1) + '%') : '—' }}
                  </template>
                </div>
              </div>

              <div class="output-chip">
                <div class="chip-label">Last Updated</div>
                <div class="chip-value">
                  <div v-if="ocrStatus === 'loading'" class="skeleton skeleton-text"></div>
                  <template v-else>
                    {{ parseAgo }}
                  </template>
                </div>
              </div>
            </div>

            <label class="muted-label" style="margin-top:8px;">Parsed Text</label>
            <div class="output-panel" aria-live="polite" role="status">
              <div v-if="ocrStatus === 'loading'" class="skeleton skeleton-block"></div>
              <div class="output-text" v-else-if="parsedText && parsedText !== '—'">{{ parsedText }}</div>
              <div class="output-empty" v-else>— no parsed text —</div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-col">
        <div class="stream-box category-box">
          <h3 class="category-title">OCR Settings</h3>
          <div class="category-body">
            <div class="form-field">
              <label>OCR Engine</label>
              <select v-model="ocrEngine">
                <option v-for="opt in ocrEngineOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>

            <div class="form-field">
              <label>Highlight Color</label>
              <ColorPicker v-model="selectedColor" />
            </div>

            <div style="margin-top:8px; display:flex; gap:12px; align-items:center;">
              <button
                class="run-button"
                @click="runOCR"
                :disabled="ocrTriggering || isSaving"
                :class="{ 'disabled': ocrTriggering || isSaving }"
              >
                <span class="button-content">
                  <span class="spinner" v-if="ocrTriggering"></span>
                  <span class="text" :class="{ invisible: ocrTriggering }">Run OCR</span>
                </span>
              </button>

              <button
                class="save-button"
                @click="saveOCRSettings"
                :disabled="isCleanForm || isSaving"
                :class="{ 'disabled': isCleanForm || isSaving }"
              >
                <span class="button-content">
                  <span class="spinner" v-if="isSaving"></span>
                  <span class="text" :class="{ invisible: isSaving }">Save Settings</span>
                </span>
              </button>

              <div style="color:#aaa; font-size:0.95rem;">{{ isCleanForm ? 'Saved' : 'Unsaved changes' }}</div>
            </div>
          </div>
        </div>

        <div class="stream-box category-box">
          <h3 class="category-title">Runtime</h3>
          <div class="category-body">
            <div class="radio-row"><strong>Engine:</strong>&nbsp;<span style="color:#ccc">{{ ocrEngine }}</span></div>
            <div class="radio-row"><strong>OCR running:</strong>&nbsp;<span style="color:#ccc">{{ ocrRunning ? 'yes' : 'no' }}</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* small additions for run button + existing styles kept */
.run-button {
  position: relative;
  align-self: flex-start;
  background: transparent;
  color: #40F284;
  border: 1px solid #40F284;
  padding: 10px 14px;
  border-radius: 6px;
  font-weight: 700;
  cursor: pointer;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.run-button.disabled { opacity:0.45; cursor:not-allowed; pointer-events:none; }

/* existing spinner/text classes reused */
.button-content { position:relative; display:flex; align-items:center; justify-content:center; }
.spinner { position:absolute; width:16px; height:16px; border:3px solid black; border-top:3px solid transparent; border-radius:50%; animation:spin 0.8s linear infinite; }
.text { transition: opacity 0.2s ease; }
.invisible { opacity:0; }

/* rest of your existing style (kept) */
.chip-label {
  font-size:0.72rem;
  color:#9aa0a6;
  text-transform:uppercase;
  letter-spacing:0.06em;
}
.output-panel {
  background: transparent;
  border: none;
  padding: 6px 0;
}
.output-text {
  white-space: pre-wrap;        
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", monospace;
  font-size: 0.98rem;
  line-height: 1.45;
  color: #e6e6e6;
  padding: 12px;
}
.output-empty {
  color: #9aa0a6;
  font-style: italic;
  padding: 10px 12px;
}
.output-meta {
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  align-items:center;
}

.output-chip {
  display:flex;
  flex-direction:column;
  gap:4px;
  padding:8px 12px;
  border-radius:999px;                
  font-size:0.9rem;
  color:#e9eef0;
  min-width: 96px;
}
.chip-value {
  font-weight:700;
  font-size:0.95rem;
  color:#ffffff;
  line-height:1;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}


.ocr-root { 
  display:flex; 
  flex-direction:column; 
  gap:16px; color:white; 
}
.skeleton {
  background: #2d3038;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}

.skeleton::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(74, 77, 87, 0.3),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

.skeleton-text {
  width: 80px;
  height: 14px;
}

.skeleton-block {
  width: 100%;
  height: 64px; /* or match average text block size */
  margin-top: 6px;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}
  
.section-title { font-size:1.5rem; font-weight:600; }

.ocr-layout { 
  display: flex; 
  gap: 20px; 
  align-items: start; 
  flex-wrap: wrap;
}
.left-col { 
  display: flex; 
  flex-direction: column; 
  gap: 12px; 
  flex: 1 1 500px;
  min-width: 0;
}
.right-col { 
  display: flex; 
  flex-direction: column; 
  gap: 12px; 
  flex: 0 1 320px;
  min-width: 280px;
}

@media (max-width: 900px) {
  .ocr-layout {
    flex-direction: column;
  }
  .left-col, .right-col {
    flex: 1 1 100%;
    width: 100%;
  }
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

.radio-row, .checkbox-row { display:flex; align-items:center; gap:8px; color:#ddd; font-size:0.98rem; }
.form-field { display:flex; flex-direction:column; gap:6px; }
label { color:#aaa; font-size:0.95rem; }

input[type="text"], input[type="number"], select {
  background: #1e1f25;
  color: white;
  border: 1px solid #2d2f37;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.98rem;
}

.image-wrapper { width:100%; display:flex; justify-content:center; align-items:center; }
.parsed-image {
  width:100%;
  max-height:420px;
  object-fit: contain;
  border-radius:8px;
  background:#111;
  border:1px solid #2d2f37;
  display:block;
}

.readonly { opacity:0.95; }
.readonly-value {
  background:#15161a;
  border-radius:6px;
  padding:10px;
  font-size:0.95rem;
  color:#e6e6e6;
  border:1px solid #2d2f37;
  white-space:pre-wrap;
  word-break:break-word;
}

.text-output {
  min-height:90px;
  max-height:340px;
  overflow:auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", monospace;
  font-size:0.95rem;
}

.save-button {
  position: relative;
  align-self: flex-start;
  background-color: #40F284;
  color: black;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  min-width: 140px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.save-button.disabled { background-color:#444; color:#999; cursor:not-allowed; }
.save-button:disabled { pointer-events:none; }

@keyframes spin { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }

.status-dot { width: 10px; height: 10px; border-radius: 50%; display:inline-block; background:#4a4d57; }
.status-dot.online { background:#40F284; }
.status-dot.error { background:#f25540; }
.status-dot.loading { background:#4a4d57; }
</style>
