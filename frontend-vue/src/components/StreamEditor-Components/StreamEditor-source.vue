<script setup>
import { ref, computed, watch } from 'vue'
import { EoesStream } from '../../models/EoesStream.js'
import StreamPreview from '../StreamPreview.vue'

const props = defineProps({
  stream: {
    type: EoesStream,
    required: true
  }
})

const emit = defineEmits(['save'])

const editedName = ref(props.stream.name)
const editedRtspUrl = ref(props.stream.url)
const saving = ref(false)

watch(() => props.stream, (newStream) => {
  editedName.value = newStream.name
  editedRtspUrl.value = newStream.url
})

// Debounce the preview stream source so it doesn't update instantly
const debouncedStreamSource = ref(editedRtspUrl.value)
let debounceTimeout
watch(editedRtspUrl, (val) => {
  clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    debouncedStreamSource.value = val
  }, 500)
})

const isDirty = computed(() => {
  return editedName.value !== props.stream.name || editedRtspUrl.value !== props.stream.url
})

async function saveChanges() {
  if (!isDirty.value || saving.value) return
  saving.value = true

  try {
    const response = await fetch(`/streams/${props.stream.name}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: props.stream.name, // currently it doesn't work to change the name of the stream
        stream_src: editedRtspUrl.value
      })
    })

    if (!response.ok) {
      throw new Error('Failed to save changes')
    } else {
      // Update the stream object with new values so the isDirty computed property updates
      props.stream.url = editedRtspUrl.value
      props.stream.name = editedName.value
    }


    emit('save', props.stream)
  } catch (error) {
    console.error('Error saving changes:', error)
    alert('Error saving changes:', error) // TODO: better error handling
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="source-view">
    <h2 class="section-title">Edit Stream Source</h2>
    <div class="seperator">
      <div class="preview-grid">
        <label class="preview-label">Preview</label>
        <StreamPreview :streamid="editedName" :previewStreamSource="debouncedStreamSource" preview="true" />
      </div>
      <div class="form-grid">
        <div class="form-field">
          <label for="name">Stream Name</label>
          <input id="name" v-model="editedName" disabled type="text" placeholder="Enter stream name" />
        </div>

        <div class="form-field">
          <label for="rtsp">Source URL</label>
          <input id="rtsp" v-model="editedRtspUrl" type="text" placeholder="rtsp://..." />
        </div>
        <button 
          class="save-button" 
          @click="saveChanges"
          :disabled="!isDirty || saving"
          :class="{ 'disabled': !isDirty || saving }"
        >
          <span class="button-content">
            <span class="spinner" v-if="saving"></span>
            <span class="text" :class="{ invisible: saving }">Save Changes</span>
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.source-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: white;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
}

.form-grid {
  grid-area: form-grid;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
}

label {
  font-size: 0.95rem;
  margin-bottom: 6px;
  color: #aaa;
}

input {
  background: #1e1f25;
  color: white;
  border: 1px solid #2d2f37;
  border-radius: 6px;
  padding: 10px;
  font-size: 1rem;
}

.save-button {
  position: relative;
  margin-top: 10px;
  align-self: flex-start;
  background-color: #40F284;
  color: black;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  min-width: 140px; /* optional, to keep consistent width */
  min-height: 42px; /* ensure consistent height */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.save-button:hover {
  background-color: #36c96c;
}

.save-button.disabled {
  background-color: #444;
  color: #999;
  cursor: not-allowed;
}

.save-button:disabled {
  pointer-events: none;
}

.button-content {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  position: absolute;
  width: 16px;
  height: 16px;
  border: 3px solid black;
  border-top: 3px solid transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.text {
  transition: opacity 0.2s ease;
}
.preview-grid {
  grid-area: preview-grid;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-label {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.invisible {
  opacity: 0;
}
  
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.seperator {
  display: grid; 
  grid-template-columns: 1fr 300px; 
  grid-template-rows: 1fr; 
  gap: 0px 0px; 
  grid-template-areas: 
    "form-grid preview-grid"; 
}

</style>
