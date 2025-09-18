<script setup>
import { defineEmits, defineProps } from 'vue'
import { Icon } from '@iconify/vue'

const emit = defineEmits(['close-overlay'])

const props = defineProps({
  title: String,
  height: {
    type: String,
    default: "66%"
  },
  width: {
    type: String,
    default: "33%"
  },
})

const closeOverlay = () => {
  emit('close-overlay')
}
</script>

<template>
  <div class="overlay">
    <div class="overlay-inner" :style="{ width: props.width, height: props.height }">
      <div class="overlay-header">
        <h1>{{ props.title }}</h1>
        <button class="close-overlay" @click="closeOverlay">
          <Icon icon="mdi-close" style="font-size: 32px; color: #4A4D57;" />
        </button>
      </div>
      <div class="overlay-content">
        <slot name="content" /> 
      </div>
      <div class="overlay-footer">
        <slot name="footer" /> 
      </div>
    </div>
  </div>
</template>


<style scoped>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(10px);
  background-color: rgba(0, 0, 0, 0.3); /* Optional dark tint */
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.overlay-inner {
  border-radius: 15px;
  border: solid 2px #23252C;
  position: relative;
  padding: 20px;
  padding-left: 27px;
  padding-right: 27px;
  text-align: center;
  width: v-bind(width);
  height: v-bind(height);
  min-height: 240px;
  min-width: 350px;
  background-color: #181A1E;
  display: grid; 
  grid-template-columns: 1fr; 
  grid-template-rows: 60px 1fr 50px; 
  gap: 0px 0px; 
  grid-template-areas: 
      "overlay-header"
      "overlay-content"
      "overlay-footer"; 
}

.overlay-header { 
  grid-area: overlay-header; 
}

.overlay-header h1 {
  margin: 0;
  color: white;
  text-align: left;
  font-family: "Roboto", sans-serif;
  font-size: 1.5rem;
}

.overlay-footer { 
  grid-area: overlay-footer; 
  display: flex;
  justify-content: space-between;
  flex-direction: row;
}
.overlay-content { 
  grid-area: overlay-content; 
  text-align: left;
}

.close-overlay {
  position: absolute;
  top: 18px;
  right: 18px;
  background: none;
  border: none;
  cursor: pointer;
}

.overlay-fade-enter-active {
  transition: opacity 0.4s ease-in;
}
.overlay-fade-leave-active {
  transition: opacity 0.3s ease-out;
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
