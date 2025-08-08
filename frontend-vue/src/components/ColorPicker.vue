<template>
  <div class="color-picker-wrapper" ref="wrapper">
    <button
      class="color-button"
      :style="{ backgroundColor: displayColor }"
      @click="togglePicker"
      aria-label="Open color picker"
    ></button>

    <teleport to="body">
      <div
        v-if="showPicker"
        class="color-picker-popup"
        :style="popupStyle"
        ref="popup"
      >
        <canvas id="myCanvas" width="200" height="200" style="border-radius:50%; background-color:rgba(255,255,255,0); touch-action: none;">
            Your browser does not support this color picker
        </canvas>

        <div class="sliders">
          <label>R: <input type="range" min="0" max="255" v-model.number="r" @input="onRgbChange" /></label>
          <label>G: <input type="range" min="0" max="255" v-model.number="g" @input="onRgbChange" /></label>
          <label>B: <input type="range" min="0" max="255" v-model.number="b" @input="onRgbChange" /></label>
        </div>
        <input
          type="text"
          v-model="hex"
          @input="onHexInput"
          placeholder="#RRGGBB"
          id="color-hex-input"
        />
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '#ff0000'
  }
})
const emit = defineEmits(['update:modelValue'])

const wrapper = ref(null)
const popup = ref(null)
const showPicker = ref(false)
const popupStyle = ref({})

const r = ref(255)
const g = ref(0)
const b = ref(0)
const hex = ref(props.modelValue)

// internal HSV & selector pos
const hue = ref(0)        // 0..360
const sat = ref(1)        // 0..1
const val = ref(1)        // 0..1
const selector = ref({ x: 0, y: 0 })

const displayColor = computed(() => `rgb(${r.value}, ${g.value}, ${b.value})`)

function clamp(n, a, c) { return Math.min(c, Math.max(a, n)) }

function hexToRgb(hexColor) {
  const match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hexColor)
  return match ? {
    r: parseInt(match[1], 16),
    g: parseInt(match[2], 16),
    b: parseInt(match[3], 16)
  } : null
}

function rgbToHex(rr, gg, bb) {
  return `#${[rr, gg, bb].map(x => x.toString(16).padStart(2, '0')).join('')}`
}

// standard conversions
function hsvToRgb(h, s, v) {
  // h in [0,360), s,v in [0,1]
  let c = v * s
  let x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  let m = v - c
  let r1, g1, b1
  if (h < 60)      { r1 = c; g1 = x; b1 = 0 }
  else if (h < 120){ r1 = x; g1 = c; b1 = 0 }
  else if (h < 180){ r1 = 0; g1 = c; b1 = x }
  else if (h < 240){ r1 = 0; g1 = x; b1 = c }
  else if (h < 300){ r1 = x; g1 = 0; b1 = c }
  else             { r1 = c; g1 = 0; b1 = x }
  return [
    Math.round((r1 + m) * 255),
    Math.round((g1 + m) * 255),
    Math.round((b1 + m) * 255)
  ]
}

function rgbToHsv(rr, gg, bb) {
  const rN = rr / 255, gN = gg / 255, bN = bb / 255
  const mx = Math.max(rN, gN, bN)
  const mn = Math.min(rN, gN, bN)
  const d = mx - mn
  let h = 0
  if (d === 0) h = 0
  else if (mx === rN) h = 60 * (((gN - bN) / d) % 6)
  else if (mx === gN) h = 60 * (((bN - rN) / d) + 2)
  else h = 60 * (((rN - gN) / d) + 4)
  if (h < 0) h += 360
  const s = mx === 0 ? 0 : d / mx
  const v = mx
  return { h, s, v }
}

let canvasEl = null
let ctx = null
let dpr = 1
let width = 200
let height = 200
let centerX = 100
let centerY = 100
let maxRadius = 100
let pointerDown = false

function drawWheel() {
  if (!ctx || !canvasEl) return
  // clear
  ctx.clearRect(0, 0, canvasEl.width, canvasEl.height)

  // draw color wheel by per-pixel (scaled for DPR)
  const w = width * dpr
  const h = height * dpr
  const imageData = ctx.createImageData(w, h)
  const cx = centerX * dpr
  const cy = centerY * dpr
  const radius = maxRadius * dpr

  for (let i = 0; i < imageData.data.length; i += 4) {
    const pixelIndex = i / 4
    const x = pixelIndex % w
    const y = Math.floor(pixelIndex / w)
    const dx = x - cx
    const dy = y - cy
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist <= radius) {
      let angle = Math.atan2(dy, dx) * (180 / Math.PI)
      if (angle < 0) angle += 360
      const saturation = dist / radius
      const [rr, gg, bb] = hsvToRgb(angle, saturation, 1)
      imageData.data[i + 0] = rr
      imageData.data[i + 1] = gg
      imageData.data[i + 2] = bb
      imageData.data[i + 3] = 255
    } else {
      imageData.data[i + 0] = 0
      imageData.data[i + 1] = 0
      imageData.data[i + 2] = 0
      imageData.data[i + 3] = 0
    }
  }

  // Put image data scaled into context (we created it at DPR resolution)
  // But canvas is already scaled for DPR; so write at 0,0 with w,h
  ctx.putImageData(imageData, 0, 0)

  // draw selection marker (scale back to logical pixels)
  drawSelector()
}

function drawSelector() {
  if (!ctx || !canvasEl) return
  const sx = selector.value.x * dpr
  const sy = selector.value.y * dpr
  // Outer ring
  ctx.beginPath()
  ctx.lineWidth = 3 * dpr
  ctx.strokeStyle = 'white'
  ctx.arc(sx, sy, 8 * dpr, 0, Math.PI * 2)
  ctx.stroke()
  // inner ring dark
  ctx.beginPath()
  ctx.lineWidth = 1 * dpr
  ctx.strokeStyle = 'black'
  ctx.arc(sx, sy, 8 * dpr, 0, Math.PI * 2)
  ctx.stroke()
}

function posToHs(x, y) {
  // x,y are logical (CSS) pixel coords relative to canvas top-left
  const dx = x - centerX
  const dy = y - centerY
  let dist = Math.sqrt(dx * dx + dy * dy)
  const angle = Math.atan2(dy, dx) * (180 / Math.PI)
  let h = angle < 0 ? angle + 360 : angle
  let s = clamp(dist / maxRadius, 0, 1)
  return { h, s, inside: dist <= maxRadius, dx, dy, dist }
}

function hsToPos(h, s) {
  const rad = (h * Math.PI) / 180
  const r = s * maxRadius
  return {
    x: centerX + Math.cos(rad) * r,
    y: centerY + Math.sin(rad) * r
  }
}

function setFromHs(h, s, v = 1) {
  hue.value = h
  sat.value = s
  val.value = v
  const [rr, gg, bb] = hsvToRgb(h, s, v)
  r.value = rr; g.value = gg; b.value = bb
  hex.value = rgbToHex(rr, gg, bb)
  // update selector position
  const pos = hsToPos(h, s)
  selector.value.x = pos.x
  selector.value.y = pos.y
  // redraw wheel + selector
  drawWheel()
  emit('update:modelValue', hex.value)
}

function onPointerDown(e) {
  if (!canvasEl) return
  pointerDown = true
  canvasEl.setPointerCapture(e.pointerId)
  handlePointer(e)
}

function onPointerUp(e) {
  if (!canvasEl) return
  try { canvasEl.releasePointerCapture(e.pointerId) } catch {}
  pointerDown = false
}

function onPointerMove(e) {
  if (!pointerDown) return
  handlePointer(e)
}

function handlePointer(e) {
  if (!canvasEl) return
  const rect = canvasEl.getBoundingClientRect()
  // clientX/Y -> logical canvas coords
  const x = clamp((e.clientX - rect.left), 0, rect.width)
  const y = clamp((e.clientY - rect.top), 0, rect.height)

  const { h, s, inside, dist } = posToHs(x, y)
  // If outside the wheel, clamp the selection to the rim for saturation 1
  const useS = inside ? s : clamp(1, 0, 1) * clamp(dist / dist, 0, 1) // keep 1 for rim
  // better: clamp to edge: s = min(1, dist/maxRadius)
  const sClamped = clamp(dist / maxRadius, 0, 1)
  const finalS = inside ? s : sClamped

  // update selector pos to clamped position on the rim if outside
  const pos = hsToPos(h, finalS)
  selector.value.x = pos.x
  selector.value.y = pos.y

  setFromHs(h, finalS, 1)
}

function onRgbChange() {
  // when sliders change -> compute HSV, update selector, hex, emit
  const { h, s, v } = rgbToHsv(r.value, g.value, b.value)
  setFromHs(h, s, v)
}

function onHexInput() {
  const rgbVal = hexToRgb(hex.value)
  if (rgbVal) {
    r.value = rgbVal.r
    g.value = rgbVal.g
    b.value = rgbVal.b
    const { h, s, v } = rgbToHsv(r.value, g.value, b.value)
    setFromHs(h, s, v)
  }
}

function togglePicker() {
  showPicker.value = !showPicker.value
  if (showPicker.value) {
    nextTick(() => {
      const rect = wrapper.value.getBoundingClientRect()
      popupStyle.value = {
        position: 'absolute',
        top: `${rect.bottom + window.scrollY}px`,
        left: `${rect.left + window.scrollX}px`
      }
      // get canvas and initialize drawing
      initCanvas()
      drawWheel()
    })
  }
}

function handleClickOutside(e) {
  if (
    showPicker.value &&
    wrapper.value &&
    !wrapper.value.contains(e.target) &&
    popup.value &&
    !popup.value.contains(e.target)
  ) {
    showPicker.value = false
  }
}

function initCanvas() {
  canvasEl = document.getElementById('myCanvas')
  if (!canvasEl) return
  // logical CSS size
  width = canvasEl.width
  height = canvasEl.height
  dpr = window.devicePixelRatio || 1
  // scale for DPR to keep crisp pixels
  canvasEl.width = Math.round(width * dpr)
  canvasEl.height = Math.round(height * dpr)
  canvasEl.style.width = width + 'px'
  canvasEl.style.height = height + 'px'
  ctx = canvasEl.getContext('2d')
  ctx.setTransform(1,0,0,1,0,0) // reset
  // since we created imageData at DPR resolution, no extra scaling is necessary.
  centerX = width / 2
  centerY = height / 2
  maxRadius = Math.min(width, height) / 2

  // pointer events
  canvasEl.addEventListener('pointerdown', onPointerDown)
  window.addEventListener('pointerup', onPointerUp)
  canvasEl.addEventListener('pointermove', onPointerMove)

  // position selector according to current rgb/hsv
  const { h, s, v } = rgbToHsv(r.value, g.value, b.value)
  hue.value = h; sat.value = s; val.value = v
  const pos = hsToPos(h, s)
  selector.value.x = pos.x
  selector.value.y = pos.y
}

onMounted(() => {
  const rgb = hexToRgb(props.modelValue)
  if (rgb) {
    r.value = rgb.r
    g.value = rgb.g
    b.value = rgb.b
  }
  document.addEventListener('click', handleClickOutside)
})

watch(showPicker, async (nv) => {
  if (nv) {
    await nextTick()
    initCanvas()
    drawWheel()
  } else {
    // cleanup pointer capture if needed
    if (canvasEl) {
      try { canvasEl.releasePointerCapture && canvasEl.releasePointerCapture() } catch {}
    }
  }
})

// Keep wheel in sync if external modelValue changes
watch(() => props.modelValue, (newVal) => {
  if (!newVal) return
  const rgb = hexToRgb(newVal)
  if (rgb) {
    r.value = rgb.r; g.value = rgb.g; b.value = rgb.b
    const { h, s, v } = rgbToHsv(r.value, g.value, b.value)
    hue.value = h; sat.value = s; val.value = v
    const pos = hsToPos(h, s)
    selector.value.x = pos.x; selector.value.y = pos.y
    // redraw if open
    if (showPicker.value) drawWheel()
  }
})

// keep canvas redraw when sliders/hex change outside pointer movement
watch([r, g, b], () => {
  if (showPicker.value) {
    const { h, s, v } = rgbToHsv(r.value, g.value, b.value)
    hue.value = h; sat.value = s; val.value = v
    const pos = hsToPos(h, s)
    selector.value.x = pos.x; selector.value.y = pos.y
    drawWheel()
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  if (canvasEl) {
    canvasEl.removeEventListener('pointerdown', onPointerDown)
    canvasEl.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
  }
})
</script>

<style scoped>
.color-picker-wrapper {
    display: inline-block;
}

#color-hex-input {
    box-sizing: border-box;
    margin-top: 8px;
    width: calc(100% - 8px);
}

.color-button {
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
.color-picker-popup {
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    width: auto;
    height: auto;
    background-color: #2d2f37;
}
.sliders label {
    display: flex;
    align-items: center;
    font-size: 12px;
    gap: 4px;
    color: #ddd;
}
.sliders input[type=range] {
    flex: 1;
}
.color-picker-popup input[type="text"] {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px;
    font-family: monospace;
    width: 100%;
}
</style>
