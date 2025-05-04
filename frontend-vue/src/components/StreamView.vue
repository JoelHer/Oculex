<script setup>
import { ref, onMounted,onBeforeUnmount, computed, watch } from 'vue'
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

const addStreamByOverlay = () => {
  const streamName = newStreamName.value
  const streamSource = newStreamSource.value

  if (streamName && streamSource) {
    //make a post request to add the stream
    console.log('Adding stream:', streamName, streamSource);
    const response = fetch('/streams/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: streamName, stream_src: streamSource })
    }).then(response => {
      if (response.ok) {
        console.log('Stream added successfully')
        streams.value.push(streamName)
        newStreamName.value = 'awesome-stream-name'
        newStreamSource.value = 'rtsp://user:password@host/h264'
        closeOverlay()
      } else {
        console.error('Failed to add stream:', response.status)
      }
    }).catch(error => {
      console.error('Error adding stream:', error)
    })
  } else {
    console.error('Stream name and source are required')
  }
}

const invalidNameReason = ref('')

const isNameValid = computed(() => {
  if( /^[a-zA-Z0-9-_]{3,35}$/.test(newStreamName.value)) {
    invalidNameReason.value = ''
    return true
  } else {
    invalidNameReason.value = 'Error. Allowed: a-z, 0-9, -, _, 3-35 Characters allowed.'
    return false
  }
})

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

const toggleEditMode = () => {
  editMode.value = !editMode.value
}

const newStreamName = ref("awesome-stream-name")
const newStreamSource = ref("rtsp://user:password@host/h264")
const editMode = ref(false)
const debouncedStreamSource = ref(newStreamSource.value)
let debounceTimeout

watch(newStreamSource, (val) => {
  clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    debouncedStreamSource.value = val
  }, 500)
})
</script>

<template>
  <div class="streamView">
    <div id="streamFlexbox">
      <StreamPreview
          v-for="stream in streams"
          :key="stream"
          :streamid="stream"
      />
      <StreamPreviewAdd v-if="editMode" @click="openOverlay"/>
    </div>
    <transition name="overlay-fade">
      <Overlay v-if="showOverlay" title="Add Stream" @close-overlay="closeOverlay">
        <template #content>
          <div class="addStream">
            <div class="addStream-left">
              <p>Stream name</p>
              <input v-model="newStreamName" type="text" placeholder="awesome-stream-name" :class="{ invalidname: !isNameValid }" />
              <div class="invalidnameTextWrapper">
                <p class="invalidnameText" :class="{ hidden: isNameValid }">{{ invalidNameReason }}</p>
              </div>
              <p>Stream source</p>
              <input v-model="newStreamSource" type="text" placeholder="rtsp://user:password@host/h264" />
              <ul class="example">
                <li>
                  <label>rtsp://user:password@host/h264</label>
                </li>
                <li>
                  <label>file:///data/image.png</label>
                </li>
              </ul>
            </div>
            <div class="addStream-Right">
              <p>Preview</p>
              <StreamPreview :streamid="newStreamName" :previewStreamSource="debouncedStreamSource" preview=true />
            </div>
          </div>
        </template>
        <template #footer>
          <button class="addStreamBtn" @click="addStreamByOverlay" :disabled="!isNameValid">
            <p>Add</p>
            <Icon icon="mdi-plus" style="font-size: 20px;" />
          </button>
        </template>
      </Overlay>
    </transition>
    <button @click="toggleEditMode" class="floating-button">
      <transition name="fade-scale" mode="out-in">
        <Icon
          v-if="editMode"
          key="close"
          icon="mdi-close"
          style="font-size: 26px;"
        />
        <Icon
          v-else
          key="edit"
          icon="mdi-edit"
          style="font-size: 24px;"
        />
      </transition>
    </button>
  </div>
</template>

<style scoped>
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.2s ease;
}
.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.8);
}


.floating-button {
  width: 48px;
  height: 48px;
  position: fixed;
  bottom: 20px;    /* Distance from the bottom */
  right: 20px;     /* Distance from the right */
  padding: 0px;
  display: flex;
  justify-content: center;
  align-items: center;
  border: none;
  border-radius: 12px;
  background-color: #007bff;
  color: white;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  transition: background-color 0.3s ease;
}

.floating-button:hover {
  background-color: #0056b3;
  transition: background-color 0.3s ease;
}

.streamView {
  height: 100%;
  width: 100%;
}

.invalidname {
  color: #f25540;
}

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

.addStream {  
  display: grid;
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

.addStreamBtn {
  background-color: #406af2;
  width: 88px;
  height: 44px;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px; /* Adds spacing between the text and the icon */
  margin: 0px;
  padding-top: 3px;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.addStreamBtn p {
  padding-top: 2px;
}

.addStreamBtn:disabled {
  background-color: #4069f252;
  color: #9b9b9b;
  cursor: not-allowed;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.example {
  font-size: 0.8rem;
  color: #4a4d57;
  margin-top: 10px;
}

.example {
  margin-top: 0px;
}


.invalidnameTextWrapper {
  height: 16px; /* enough for 1 line of text */
  margin-bottom: 10px;
  overflow: hidden;
}

.invalidnameText {
  color: #f25540;
  font-size: 0.7rem !important;
  transition: opacity 0.3s;
}

.hidden {
  opacity: 0;
}

</style>
