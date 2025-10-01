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
  <div
    class="image-wrapper"
    :class="{ 'loading-ratio': loading }"
  >
    <img
      :src="streamUrl"
      class="card-image"
      @load="onImageLoad"
      @error="onImageError"
    />
    <div v-if="loading" class="skeleton"></div>
    <div v-if="error" class="fallbackIconContainer">
      <Icon icon="mdi:image-off" class="fallbackIcon" />
    </div>
  </div>
</template>

<style scoped>
.image-wrapper {
  position: relative;
  width: 100%;
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

.image-wrapper.loading-ratio {
  aspect-ratio: 16 / 9; /* default ratio */
}

.skeleton {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #2d3038; /* lighter than #23252c */
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
    rgba(74, 77, 87, 0.3), /* soft bluish-gray shimmer */
    transparent
  );
  animation: shimmer 1.5s infinite;
}


@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
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