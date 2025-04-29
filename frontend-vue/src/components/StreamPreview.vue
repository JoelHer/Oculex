<script setup>
import StreamPreview from './StreamPreview.vue'

defineProps({
  streamid: String,
})
</script>

<template>
  <div id="streamPreview">
    <p>{{ streamid }}</p>
  </div>
</template>

<style scoped>
#streamPreview {
    width: 233px;
    height: 162px;
    background-color: #23252C;
    flex-shrink: 0;
    border-radius: 15px;
}
</style>
