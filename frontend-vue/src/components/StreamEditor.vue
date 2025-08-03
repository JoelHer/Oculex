<script setup>
import { ref, onMounted } from 'vue'
import Overview from './StreamEditor-Components/StreamEditor-overview.vue'
import Ocrengine from './StreamEditor-Components/StreamEditor-ocrengine.vue'
import Source from './StreamEditor-Components/StreamEditor-source.vue'
import Parser from './StreamEditor-Components/StreamEditor-parser.vue'

import { EoesStream } from '../models/EoesStream'

const props = defineProps({
  stream: EoesStream
})

const streamId = ref(props.stream.name)

const views = [
  { id: 'overview',   label: 'Overview' },
  { id: 'source',     label: 'Source' },
  { id: 'parser',     label: 'Parser' },
  { id: 'ocrengine',  label: 'OCR Engine' },
]

const streamUrl = ref('Loading URL...')
const view = ref('overview') 

onMounted(() => {
    fetchStreamData()
        .then(data => {
            streamUrl.value = data.rtsp_url || 'No URL available'
            if (data.rtsp_url) {
              props.stream.url = data.rtsp_url
            }

        })
        .catch(error => {
            console.error('Error fetching stream data:', error)
        })
})

async function fetchStreamData() {
    console.log('Fetching stream data for:', props.stream.name)
    try {
        const response = await fetch('/streams/' + props.stream.name)
        if (response.ok) {
            const data = await response.json()
            return data
        } else {
            throw new Error('Failed to fetch streams: ' + response.status)
        }
    } catch (error) {
        throw new Error('Error fetching streams: ' + error)
    }
}
</script>

<template>
  <div class="streamEditor">
    <div class="editorNavbar">
      <div class="container titleContainer">
        <div class="back-button" @click="$emit('close')">
          <Icon icon="mdi:chevron-left" style="font-size: 30px;" />
        </div>
        <h1>Stream Editor</h1>
      </div>

      <div class="container navbarContainer">
        <div class="navbarContainer-header">
          <img 
            :src="'/thumbnail/'+streamId" 
            class="stream-thumbnail"
          />
          <div class="stream-info">
            <h1 class="stream-title">{{ streamId }}</h1>
            <p class="stream-title-description">{{ streamUrl }}</p>
          </div>
        </div>

        <div class="navbarContainer-body">
            <div class="nav-separator"></div>
            <ul class="view-selector">
                <li 
                    v-for="item in views" 
                    :key="item.id"
                    :class="{ active: view === item.id }"
                    @click="view = item.id"
                >
                    {{ item.label }}
                </li>
            </ul>
        </div>
      </div>
    </div>

    <div class="editorView">
      <Overview    v-if="view === 'overview'" :stream="props.stream" />
      <Source      v-else-if="view === 'source'" :stream="props.stream" />
      <Parser      v-else-if="view === 'parser'" :stream="props.stream"/>
      <Ocrengine   v-else-if="view === 'ocrengine'" />
    </div>
  </div>
</template>

<style scoped>
.streamEditor {  
    display: grid;
    height: 100%;
    width: 100%;
    grid-template-columns: 350px 1fr;
    grid-template-rows: 1fr;
    gap: 0px 0px;
    grid-auto-flow: row;
    grid-template-areas:
        "editorNavbar editorView";
}

.container {
    width: calc( 100% - 4px );
    min-height: 45px;
    background-color: #23252c;
    border-radius: 15px;
    border: #2d2f37 solid 2px;
}

.back-button {
    cursor: pointer;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding-left: 6px;
}

.editorNavbar { 
    gap: 10px;
    display: flex;
    flex-direction: column;
    padding: 20px;
    grid-area: editorNavbar; 
}

.titleContainer {
    display: flex;
    align-items: center;
    margin: 0px;
}

.titleContainer h1 {
    margin: 0px;
    padding: 10px;
    font-size: 1.1rem;
    color: #fff;
    font-weight: 500;
    font-family: "Roboto",sans-serif;
}

.navbarContainer {
    display: grid; 
    grid-template-rows: auto 1fr; /* Let header row size dynamically */
    grid-template-areas: 
    "navbarContainer-header"
    "navbarContainer-body"; 
}


.navbarContainer-header {
    grid-area: navbarContainer-header;
    display: flex;
    align-items: center;
    width: 100%;
    overflow: hidden;
}

.navbarContainer-body {
  grid-area: navbarContainer-body;
  padding: 10px;
  padding-top: 0px;
}

.navbarContainer-header h1 {
    margin: 0px;
    padding: 10px;
    font-size: 1.1rem;
    color: #fff;
    font-weight: 500;
    font-family: "Roboto",sans-serif;
}

.editorView { 
    grid-area: editorView;
    padding: 20px;
    padding-left: 0px;
}

.stream-thumbnail {
    margin: 15px;
    border-radius: 10px;
    width: 80px;
    height: 80px;
}

.stream-title {
    overflow-x: hidden;
    text-overflow: ellipsis;
    width: calc(100% - 20px);
    text-wrap: nowrap;
    padding: 0px;
}

.stream-title-description {
    overflow-x: hidden;
    margin: 0px;
    text-overflow: ellipsis;
    width: calc(100% - 20px);
    text-wrap: nowrap;
    padding: 0px;
    color: #797979;
    font-size: 0.9rem;
}

.view-selector {
  list-style: none;
  margin: 0;
  padding: 0;
}

.view-selector li {
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #bbb;
  transition: background-color 0.2s;
}

.view-selector li:hover {
  background-color: #2d2f37;
}

.view-selector li.active {
  background-color: #3f4250;
  color: #fff;
}

.nav-separator {
  height: 2px;
  background-color: #3b3b3b;
  margin: 12px 0;
  margin-top: 0px;
  width: 100%;
}


</style>
