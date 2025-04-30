<script setup>
import { ref, onMounted,onBeforeUnmount } from 'vue'
import StreamPreview from './StreamPreview.vue'
import StreamPreviewAdd from './StreamPreviewAdd.vue'

import Overlay from './Overlay.vue'

const showOverlay = ref(false)

const openOverlay = () => {
  showOverlay.value = true
}

const closeOverlay = () => {
  showOverlay.value = false
}

const streams = ref([])

onMounted(async () => {
  try {
    const response = await fetch('/streams')
    if (response.ok) {
      const data = await response.json()
      streams.value = data.streams 
    } else {
      console.error('Failed to fetch streams:', response.status)
    }
  } catch (error) {
    console.error('Error fetching streams:', error)
  }
})

</script>

<template>
  <div id="streamFlexbox">
    <StreamPreview
        v-for="stream in streams"
        :key="stream"
        :streamid="stream"
    />
    <StreamPreviewAdd @click="openOverlay"/>
  </div>
  <transition name="overlay-fade">
    <Overlay v-if="showOverlay" @close-overlay="closeOverlay">
      <div class="addStream">
        <div class="addStream-left">
          <p>Stream name</p>
          <input type="text" placeholder="awesome-stream-name" />
          <p>Stream source</p>
          <input type="text" placeholder="rtsp://user:password@host/h264" />
          <ul class="example">
            <li>
              <label for="stream2">rtsp://user:password@host/h264</label>
            </li>
            <li>
              <label for="stream3">file:///data/image.png</label>
            </li>
          </ul>
        </div>
        <div class="addStream-Right">
          <p>Preview</p>
          <StreamPreview streamid="awesome-stream-name" preview=true />
        </div>
      </div>
    </Overlay>
  </transition>
</template>

<style scoped>
#streamFlexbox {
  display: flex;
  flex-direction: row;
  justify-content: left;
  align-items: start;
  flex-wrap: wrap;
  height: 100%;
  width: 100%;
  padding: 37px;
  gap: 17px;
}

.addStream {  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
  gap: 0px 0px;
  grid-auto-flow: row;
  grid-template-areas:
  "addStream-left addStream-Right";
}

.addStream-left { 
  grid-area: addStream-left; 
}

.addStream p {
  margin: 0px;
  font-family: "Sofia Sans", sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
}

.addStream-left input {
  width: calc(100% - 20px);
  height: 40px;
  background-color: #23252C;
  border-radius: 5px;
  border: none;
  padding-left: 10px;
  margin-bottom: 10px;
}

.addStream-Right { 
  text-align: left;
  grid-area: addStream-Right; 
  display: flex;
  flex-direction: column;
  align-items: center;
}

.example {
  font-size: 0.8rem;
  color: #4a4d57;
  margin-top: 10px;
}

.example {
  margin-top: 0px;
}

</style>
