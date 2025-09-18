<script setup>
import { ref, computed } from 'vue'
import StreamView from './components/StreamView.vue'
import StreamEditor from './components/StreamEditor.vue'
import Overlay from './components/Overlay.vue'
import FooterComponent from './components/footerComponent.vue'
import { useWebSocket } from './websocket.js'

const currentStreamId = ref(null)

const openStreamEditor = (stream) => {
  currentStreamId.value = stream
  view.value = 'StreamEditor'
}

const { connectionStatus } = useWebSocket()
const connectionTitle = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'Connected to Server'
    case 'connecting':
      return 'Connecting to Server...'
    default:
      return 'Not Connected to Server'
  }
})

const connectionColor = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return '#40F284'
    case 'connecting':
      return '#f2b440'
    default:
      return '#f25540'
  }
})
const showOverlay = ref(false)

const view = ref('StreamView') 

</script>

<template>
  <div class="app">
    <div class="app-container">
      <StreamEditor v-if="view === 'StreamEditor'" :stream="currentStreamId" @close="view = 'StreamView'" />
      <StreamView v-else-if="view === 'StreamView'" @open-stream-editor="openStreamEditor" />
      <transition name="overlay-fade">
        <Overlay v-if="showOverlay" @update:showOverlay="showOverlay = $event">
          <h1>Overlay Content</h1>
        </Overlay>
      </transition>
    </div>
    <div class="app-footer">
      <FooterComponent :title="connectionTitle" :dotcolor="connectionColor" />
    </div>
  </div>
</template>

<style scoped>
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

.app {
  height: 100vh;
  width: 100%;
  display: grid; 
  grid-template-columns: 1fr; 
  grid-template-rows: 1fr 25px; 
  gap: 0; 
  grid-template-areas: 
    "app-container"
    "app-footer"; 
}

.app-footer {
  height: 25px;
  grid-area: app-footer;
  background-color: #23252c;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.app-container {
  grid-area: app-container;
  overflow: hidden;
}

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

#closeOverlayButton {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
}

/* Transition for overlay */
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
