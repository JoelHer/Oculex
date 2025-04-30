<script setup>
import { ref } from 'vue'
import StreamView from './components/StreamView.vue'
import Overlay from './components/Overlay.vue'

const showOverlay = ref(false)
</script>

<template>
  <StreamView />
  <transition name="overlay-fade">
    <Overlay v-if="showOverlay" @update:showOverlay="showOverlay = $event">
      <h1>Overlay Content</h1>
    </Overlay>
  </transition>
</template>

<style scoped>
#openOverlayButton,
#closeOverlayButton {
  padding: 10px 20px;
  font-size: 18px;
  margin-top: 20px;
  cursor: pointer;
}

.overlay-inner {
  text-align: center;
  position: relative;
  padding: 20px;
}

/* Close button positioned at top-right corner */
#closeOverlayButton {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
}

/* --- Transition classes for overlay --- */
.overlay-fade-enter-active {
  transition: opacity 0.3s ease-in;
}
.overlay-fade-leave-active {
  transition: opacity 0.2s ease-out;
}
.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}
.overlay-fade-enter-to,
.overlay-fade-leave-from {
  opacity: 1;
}
</style>
