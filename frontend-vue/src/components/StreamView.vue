<script setup>
import { ref } from 'vue'
import StreamPreview from './StreamPreview.vue'

const count = ref(0)
</script>

<template>
  <div id="streamFlexbox">
    <StreamPreview streamid="stream-1" />
    <StreamPreview streamid="stream-2" />
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
