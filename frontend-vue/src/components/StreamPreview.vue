<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  streamid: String,
})

const loading = ref(true) // 🔥 loading starts as true

onMounted(async () => {
  try {
    const response = await fetch('/stream/' + props.streamid)
    if (response.ok) {
      const data = await response.json()
      // do something with data
    } else {
      console.error('Failed to fetch streams:', response.status)
    }
  } catch (error) {
    console.error('Error fetching streams:', error)
  }
})

// handle image load and error
function handleLoad() {
  loading.value = false
}

function handleError() {
  loading.value = false
  console.error('Thumbnail failed to load.')
}
</script>

<template>
  <div id="streamPreview">
    <img
      :src="'/thumbnail/' + streamid"
      class="previewImage"
      @load="handleLoad"
      @error="handleError"
    />
    <div v-if="loading" class="spinner"></div> <!-- 🔥 spinner shown while loading -->
    <div class="previewFooter">
      <div class="previewStatusIndicator"></div>
      <p class="previewText">{{ streamid }}</p>
    </div>
  </div>
</template>

<style scoped>
#streamPreview {
  width: 233px;
  height: 162px;
  background-color: #23252C;
  flex-shrink: 0;
  border-radius: 15px;
  overflow: hidden;
  position: relative; 
  border: #23252C solid 1px;
}

.previewImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 15px;
  position: absolute;
  top: 0;
  left: 0;
}

.spinner {
  position: absolute;
  top: calc( 50% - 18.5px );
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

.previewFooter {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 37px;
  background-color: #23252C;
  display: flex;
  align-items: center;
}

.previewStatusIndicator {
  width: 8px;
  height: 8px;
  background-color: #40F284; 
  border-radius: 50%;
  margin-left: 13px;
}

.previewText {
  font-weight: 700;
  font-size: 1rem;
  margin-left: 13px;
  margin-top: 18px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  width: calc(100% - 54px);
}
</style>
