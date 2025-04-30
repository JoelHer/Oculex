<script setup>
import { ref, onMounted,onBeforeUnmount } from 'vue'
import StreamPreview from './StreamPreview.vue'
import StreamPreviewAdd from './StreamPreviewAdd.vue'

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
    <StreamPreviewAdd />
  </div>
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
</style>
