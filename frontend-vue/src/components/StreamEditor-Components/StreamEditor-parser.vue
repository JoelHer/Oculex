<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import StreamEditorImageWithLoader from './StreamEditor-ImageWithLoader.vue'
import Overlay from '../Overlay.vue'
import { EoesStream } from '../../models/EoesStream.js'

const now = ref(new Date())
let intervalId
onMounted(() => {
  loadSettingsAndBoxes()
  intervalId = setInterval(() => {
    now.value = new Date() // triggers reactive updates
  }, 1000)
})
onUnmounted(() => {
  clearInterval(intervalId)
})

const brightness = ref(0)
const contrast = ref(0)
const saturation = ref(0)
const rotation = ref(0)

// --- Dirty form state for image settings ---
const imageSettingsInitial = reactive({
  brightness: 100,
  contrast: -87,
  saturation: 0,
  rotation: 360
})
const imageSettingsDirty = ref(false)

function markImageSettingsDirty() {
  imageSettingsDirty.value = true
}

function resetImageSettingsDirty() {
  imageSettingsDirty.value = false
  imageSettingsInitial.brightness = brightness.value
  imageSettingsInitial.contrast = contrast.value
  imageSettingsInitial.saturation = saturation.value
  imageSettingsInitial.rotation = rotation.value
}

function saveImageSettings() {
  fetch(`/set_settings/${props.stream.name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brightness: parseFloat(brightness.value),
      contrast: parseFloat(contrast.value),
      saturation: parseFloat(saturation.value),
      rotation: parseFloat(rotation.value)
    })
  }).then(() => {
    resetImageSettingsDirty()
    reloadImage('both')
  })
}

// Watch for changes to mark dirty
watch([brightness, contrast, saturation, rotation], ([b, c, s, r]) => {
  imageSettingsDirty.value = (
    b !== imageSettingsInitial.brightness ||
    c !== imageSettingsInitial.contrast ||
    s !== imageSettingsInitial.saturation ||
    r !== imageSettingsInitial.rotation
  )
})

// Popup state for region editing
const showRegionOverlay = ref(false)
function openRegionOverlay() {
  showRegionOverlay.value = true
  nextTick(() => {
    loadSettingsAndBoxes()
  })
}
function closeRegionOverlay() {
  showRegionOverlay.value = false
}

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

// Spinner state for region overlay images
const showSpinner = ref(true)
const showSpinnerP = ref(true)
const imageKey = ref(0)
const imagePKey = ref(0)
function reloadImage(type = 'both') {
  if (type === 'preview' || type === 'both') {
    imageKey.value++
    showSpinner.value = true
  }
  if (type === 'processed' || type === 'both') {
    imagePKey.value++
    showSpinnerP.value = true
  }
}
function onRegionImageLoad() {
  showSpinner.value = false
}
function onRegionImageError() {
  showSpinner.value = false
}
function onRegionImagePLoad() {
  showSpinnerP.value = false
}
function onRegionImagePError() {
  showSpinnerP.value = false
}
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

// --- Region Editor State ---
const crop_top = ref(0)
const crop_bottom = ref(0)
const crop_left = ref(0)
const crop_right = ref(0)
const coordinates = ref('')
const boxes = ref([])
const selectedBoxId = ref(null)
const selection = reactive({
  active: false,
  startX: 0,
  startY: 0,
  endX: 0,
  endY: 0,
  style: {
    left: '0px',
    top: '0px',
    width: '0px',
    height: '0px',
    display: 'none',
  }
})
// --- True image pixel mapping ---
const trueImageSize = reactive({ width: 0, height: 0 })

function getScale(img) {
  // img: HTMLImageElement
  return {
    x: img.naturalWidth / img.width,
    y: img.naturalHeight / img.height
  }
}

function mouseDown(e) {
  const img = e.target
  const rect = img.getBoundingClientRect()
  const scale = getScale(img)
  selection.active = true
  selection.startX = (e.clientX - rect.left) * scale.x
  selection.startY = (e.clientY - rect.top) * scale.y
  selection.endX = selection.startX
  selection.endY = selection.startY
  trueImageSize.width = img.naturalWidth
  trueImageSize.height = img.naturalHeight
  updateSelectionStyle()
}
function mouseMove(e) {
  if (!selection.active) return
  const img = e.target
  const rect = img.getBoundingClientRect()
  const scale = getScale(img)
  selection.endX = Math.max(0, Math.min((e.clientX - rect.left) * scale.x, img.naturalWidth))
  selection.endY = Math.max(0, Math.min((e.clientY - rect.top) * scale.y, img.naturalHeight))
  updateSelectionStyle()
}
function mouseUp(e) {
  selection.active = false
  updateSelectionStyle()
}
function updateSelectionStyle() {
  // For display, convert true image pixels to displayed image pixels
  const img = document.getElementById('image')
  if (!img) return
  const scale = img.width / img.naturalWidth
  const x = Math.min(selection.startX, selection.endX)
  const y = Math.min(selection.startY, selection.endY)
  const w = Math.abs(selection.endX - selection.startX)
  const h = Math.abs(selection.endY - selection.startY)
  selection.style.left = (x * scale) + 'px'
  selection.style.top = (y * scale) + 'px'
  selection.style.width = (w * scale) + 'px'
  selection.style.height = (h * scale) + 'px'
  selection.style.display = w > 0 && h > 0 ? 'block' : 'none'
  coordinates.value = w > 0 && h > 0 ? `x:${Math.round(x)}, y:${Math.round(y)}, w:${Math.round(w)}, h:${Math.round(h)}` : ''
}
function addBox() {
  if (selection.style.display === 'block') {
    // short integer, based on the Nth box added
    const newId = boxes.value.length > 0 ? Math.max(...boxes.value.map(b => b.id)) + 1 : 1
    // Save true image pixel coordinates
    const x = Math.min(selection.startX, selection.endX)
    const y = Math.min(selection.startY, selection.endY)
    const w = Math.abs(selection.endX - selection.startX)
    const h = Math.abs(selection.endY - selection.startY)
    boxes.value.push({
      id: newId,
      left: Math.round(x),
      top: Math.round(y),
      width: Math.round(w),
      height: Math.round(h)
    })
    selection.style.display = 'none'
    coordinates.value = ''
    saveBoxes()
  }
}
function selectBox(boxId) {
  selectedBoxId.value = boxId
}
function removeBox(boxId) {
  boxes.value = boxes.value.filter(b => b.id !== boxId)
  saveBoxes()
}
async function loadSettingsAndBoxes() {
  try {
    const settingsRes = await fetch(`/get_settings/${props.stream.name}`)
    if (settingsRes.ok) {
      const settings = await settingsRes.json()
      crop_top.value = settings.crop_top || 0
      crop_bottom.value = settings.crop_bottom || 0
      crop_left.value = settings.crop_left || 0
      crop_right.value = settings.crop_right || 0
      brightness.value = settings.brightness || 0
      contrast.value = settings.contrast || 0
      saturation.value = settings.saturation || 0
      rotation.value = settings.rotation || 0
    }
    resetImageSettingsDirty()
    console.log('Settings loaded:', {
      crop_top: crop_top.value,
      crop_bottom: crop_bottom.value,
      crop_left: crop_left.value,
      crop_right: crop_right.value
    })
    const boxesRes = await fetch(`/get_boxes/${props.stream.name}`)
    if (boxesRes.ok) {
      const data = await boxesRes.json()
      boxes.value = (Array.isArray(data) ? data : (data.boxes || [])).map(b => ({
        id: b.id || Date.now(),
        left: b.box_left,
        top: b.box_top,
        width: b.box_width,
        height: b.box_height
      }))
    }
  } catch (e) {}
}
async function saveBoxes() {
  await fetch(`/set_boxes/${props.stream.name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(boxes.value.map(b => ({
      id: b.id,
      box_left: b.left,
      box_top: b.top,
      box_width: b.width,
      box_height: b.height
    })))
  }).then(() => {
    reloadImage('both')
  })
}
async function saveSettings() {
  await fetch(`/set_settings/${props.stream.name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      crop_top: crop_top.value,
      crop_bottom: crop_bottom.value,
      crop_left: crop_left.value,
      crop_right: crop_right.value
    })
  }).then(() => {
    reloadImage('both')
  })
}
</script>
<template>
  <div class="parser-settings">
    <h2 class="section-title">Parser Settings</h2>
    <div class="parser-grid">
      <div class="stream-box">
        <div style="position:relative;">
          <StreamEditorImageWithLoader 
            :streamUrl="`/snapshot/${encodeURIComponent(props.stream.name)}?cb=${imageKey}`"
            @error="onImageError"
            class="stream-img"
            :key="imageKey"
          />
          <button class="preview-upper-navbar-right" style="position:absolute;top:10px;right:10px;z-index:2;" @click="reloadImage('preview')">
            <span class="material-icons">refresh</span>
          </button>
        </div>
        <div class="region-section">
          <button class="edit-regions-button" @click="openRegionOverlay">Edit Regions</button>

        </div>

        <div class="image-settings">

            <div class="slider-row">
              <label>Brightness</label>
              <input type="range" v-model="brightness" min="-100" max="100" />
              <span class="slider-value">{{ brightness }}</span>
            </div>
            <div class="slider-row">
              <label>Contrast (must not be 0)</label>
              <input type="range" v-model="contrast" min="-5" max="5" />
              <span class="slider-value">{{ contrast }}</span>
            </div>
            <div class="slider-row">
              <label>Rotation</label>
              <input type="range" v-model="rotation" min="0" max="360" />
              <span class="slider-value">{{ rotation }}</span>
            </div>
            <button
              :class="['image-settings-save-btn', { dirty: imageSettingsDirty }]"
              @click="saveImageSettings"
              :disabled="!imageSettingsDirty"
              style="margin-top:12px;"
            >
              <span v-if="imageSettingsDirty">Save (Unsaved)</span>
              <span v-else>Saved</span>
            </button>
        </div>
      </div>
      <div class="output-box">
        <div class="converted">
          <div style="position:relative;">
            <StreamEditorImageWithLoader 
              :streamUrl="`/snapshot/${encodeURIComponent(props.stream.name)}?cb=${imageKey}`"
              @load="onConvertedLoad"
              @error="() => onImageError('converted')"
              class="output-img"
              :key="imageKey"
            />
            <button class="preview-upper-navbar-right" style="position:absolute;top:10px;right:10px;z-index:2;" @click="reloadImage('preview')">
              <span class="material-icons">refresh</span>
            </button>
          </div>
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
          <div style="position:relative;">
            <StreamEditorImageWithLoader 
              :streamUrl="`/computed/${encodeURIComponent(props.stream.name)}?cb=${imagePKey}`"
              @load="onParsedLoad"
              @error="() => onImageError('parsed')"
              class="output-img"
              :key="imagePKey"
            />
            <button class="preview-upper-navbar-right" style="position:absolute;top:10px;right:10px;z-index:2;" @click="reloadImage('processed')">
              <span class="material-icons">refresh</span>
            </button>
          </div>
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
    <transition name="overlay-fade">
      <Overlay width="calc(100% - 100px)" height="calc(100% - 100px)" v-if="showRegionOverlay" title="Edit Regions" @close-overlay="closeRegionOverlay">
        <template #content>
          <div class="parse-container">
            <div class="parse-container-left">
              <div class="properties">
                <label>Crop Top: <input type="number" id="crop_top" min="0" v-model="crop_top"></label>
                <label>Crop Bottom: <input type="number" id="crop_bottom" min="0" v-model="crop_bottom"></label>
                <label>Crop Left: <input type="number" id="crop_left" min="0" v-model="crop_left"></label>
                <label>Crop Right: <input type="number" id="crop_right" min="0" v-model="crop_right"></label>
                <div class="coordinates">{{ coordinates }}</div>
                <button @click="addBox">Add Box</button>
                <ul>
                  <li v-for="box in boxes" :key="box.id" :class="{selected: box.id === selectedBoxId}" @click="selectBox(box.id)">
                    Box #{{ box.id }} (x:{{ box.left }}, y:{{ box.top }}, w:{{ box.width }}, h:{{ box.height }})
                    <button @click.stop="removeBox(box.id)" style="margin-left:8px;">Remove</button>
                  </li>
                </ul>
                <button @click="saveSettings">Save</button>
              </div>
            </div>
          <div class="parse-container-right">
            <div class="preview">
                    <div class="preview-upper">
                        <div class="preview-upper-navbar">
                            <h3>Stream Preview</h3>
                            <button class="preview-upper-navbar-right" @click="reloadImage('preview')">
                                <span class="material-icons">refresh</span>
                            </button>
                        </div>
                        <div class="preview-upper-content">
                    <div class="preview-container">
                        <div style="position:relative;">
                          <img id="image"
                               :src="`/snapshot/${props.stream.name}?cb=${imageKey}`"
                               :key="imageKey"
                               alt="Responsive Image"
                               draggable="false"
                               @load="onRegionImageLoad"
                               @error="onRegionImageError"
                               @mousedown="mouseDown"
                               @mousemove="mouseMove"
                               @mouseup="mouseUp"
                          >
                          <button class="preview-upper-navbar-right" style="position:absolute;top:10px;right:10px;z-index:2;" @click="reloadImage('preview')">
                            <span class="material-icons">refresh</span>
                          </button>
                        </div>
                        <div id="selection-box" class="selection-box"></div>
                        <div
                          class="selection-box"
                          v-if="selection.style.display === 'block'"
                          :style="{
                            left: selection.style.left,
                            top: selection.style.top,
                            width: selection.style.width,
                            height: selection.style.height,
                            position: 'absolute',
                            border: '2px dashed #40F284',
                            pointerEvents: 'none'
                          }"
                        ></div>
                        <div id="spinner-overlay" class="spinner-overlay" v-if="showSpinner">
                            <div class="spinner"></div>
                        </div>
                    </div>
                        </div>
                        <p class="loading-text">Loading...</p>
                    </div>
                    <div class="preview-lower">
                        <div class="preview-upper-navbar">
                            <h3>Processed Image</h3>
                            <button class="preview-upper-navbar-right" @click="reloadImage('processed')">
                                <span class="material-icons">refresh</span>
                            </button>
                        </div>
                        <div class="preview-upper-content">
                    <div class="preview-container">
                        <div style="position:relative;">
                          <img id="image-p"
                               :src="`/computed/${props.stream.name}?cb=${imagePKey}`"
                               :key="imagePKey"
                               alt="Responsive Image"
                               draggable="false"
                               @load="onRegionImagePLoad"
                               @error="onRegionImagePError"
                          >
                          <button class="preview-upper-navbar-right" style="position:absolute;top:10px;right:10px;z-index:2;" @click="reloadImage('processed')">
                            <span class="material-icons">refresh</span>
                          </button>
                        </div>
                        <div id="spinner-overlay-p" class="spinner-overlay" v-if="showSpinnerP">
                            <div class="spinner"></div>
                        </div>
                    </div>
                  </div>
                </div>
              </div>
          </div>
        </div>
        </template>
        <template #footer>
          <button class="region-save-btn" @click="closeRegionOverlay">
            <span>Done</span>
          </button>
        </template>
      </Overlay>
    </transition>
  </div>
</template>

<style scoped>
.parse-container {  display: grid;
  grid-template-columns: 326px 1fr;
  grid-template-rows: 1fr;
  gap: 0px 0px;
  grid-auto-flow: row;
  grid-template-areas:
    "parse-container-left parse-container-right";
}

.parse-container-left { grid-area: parse-container-left; }

.parse-container-right { grid-area: parse-container-right; }

#image {
  user-select: none;
}

.edit-regions-button {
  position: relative;
  margin-top: 10px;
  align-self: flex-start;
  background-color: #0060df;
  color: white;
  border: none;
  padding: 10px 10px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  min-width: 121px;
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

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
  margin-top: 10px;
}

.region-editor-popup {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.region-save-btn {
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
  font-size: 1rem;
}

.region-save-btn:hover {
  background-color: #36c96c;
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

.image-settings-save-btn.dirty {
  background-color: #f25540;
  color: white;
  border: none;
  font-weight: 700;
  box-shadow: 0 0 8px #f2554044;
}
.image-settings-save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

input[type="range"] {
  width: 100%;
}
/* --- Region Editor Popup Styling --- */
.region-editor-popup {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 0 24px 0;
  min-width: 700px;
}

.website {
  display: flex;
  flex-direction: row;
  gap: 32px;
  background: #23252c;
  border-radius: 18px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18);
  padding: 32px 40px;
  min-width: 600px;
  max-width: 900px;
}

.properties {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 260px;
  background: #23252c;
  border-radius: 12px;
  padding: 24px 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
}
.properties h1 {
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 10px;
  color: #40F284;
}
.properties label {
  font-size: 1rem;
  font-weight: 500;
  color: #eee;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.properties input[type="range"],
.properties input[type="number"] {
  margin-left: 8px;
  flex: 1;
  background: #23252c;
  border-radius: 6px;
  border: 1px solid #35363e;
  color: #fff;
  padding: 4px 6px;
}
.properties button {
  background: #40F284;
  color: #23252c;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  transition: background 0.2s;
}
.properties button:hover {
  background: #36c96c;
}
.properties #coordinates {
  font-size: 0.95rem;
  color: #40F284;
  margin: 8px 0 0 0;
}
.properties ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}
.properties ul li {
  background: #23252c;
  color: #eee;
  border-radius: 6px;
  padding: 6px 10px;
  margin-bottom: 4px;
  font-size: 0.98rem;
}

.preview {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 320px;
  align-items: stretch;
  padding-left: 18px;
}
.preview-upper, .preview-lower {
  background: #23252c;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  padding: 16px 18px;
  margin-bottom: 8px;
}
.preview-upper-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.preview-upper-navbar h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #40F284;
  margin: 0;
}
.preview-upper-navbar-right {
  background: #35363e;
  color: #40F284;
  border: none;
  border-radius: 6px;
  padding: 6px 10px;
  cursor: pointer;
  margin-left: 8px;
  transition: background 0.2s;
}
.preview-upper-navbar-right:hover {
  background: #40F284;
  color: #23252c;
}
.preview-upper-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.preview-container {
  position: relative;
  background: #181920;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-container img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  display: block;
}
.selection-box {
  position: absolute;
  border: 2px dashed #40F284;
  pointer-events: none;
}
.spinner-overlay, .spinner-overlay-p {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(35,37,44,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}
.spinner {
  border: 4px solid #35363e;
  border-top: 4px solid #40F284;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.loading-text {
  text-align: center;
  color: #aaa;
  font-size: 0.95rem;
  margin-top: 6px;
}

@media (max-width: 1100px) {
  .parser-grid {
    grid-template-columns: 1fr;
  }
}

</style>
