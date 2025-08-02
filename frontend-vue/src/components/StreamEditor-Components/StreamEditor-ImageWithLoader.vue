<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  streamUrl: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['load', 'error'])

const loading = ref(true)
const error = ref(false)

function onImageLoad() {
  loading.value = false
  error.value = false
  emit('load', props.streamUrl)
}

function onImageError() {
  loading.value = false
  error.value = true
  emit('error', props.streamUrl)
}

watch(() => props.streamUrl, () => {
  loading.value = true
  error.value = false
})
</script>

<template>
  <div class="image-wrapper">
    <img
      :src="streamUrl"
      class="card-image"
      @load="onImageLoad"
      @error="onImageError"
    />

    <div v-if="loading" class="spinner"></div>

    <div v-if="error" class="fallbackIconContainer">
      <Icon icon="mdi:image-off" class="fallbackIcon" />
    </div>
  </div>
</template>

<style scoped>
.image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #23252C;
  border-radius: 15px;
  overflow: hidden;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: 15px;
}

.spinner {
  position: absolute;
  top: calc(50% - 18.5px);
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

.fallbackIconContainer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #23252C;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallbackIcon {
  font-size: 48px;
  color: #4a4d57;
}
</style>
