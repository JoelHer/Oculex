<script setup>
import { ref } from 'vue'

defineProps({
  text: String,
  icon: String,
  bgColor: {
    type: String,
    default: '#406AF2' 
  }
})
</script>

<template>
    <button class="button" :style="{ backgroundColor: bgColor }">
      <p>{{ text }}</p>
      <Icon :icon="icon" style="font-size: 20px;" />
    </button>
</template>

<style scoped>
.button {  
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
  gap: 0px 0px;
  grid-auto-flow: row;
  grid-template-areas:
  "addStream-left addStream-Right";
}
.button p {
  margin: 0px;
  font-family: "Sofia Sans", sans-serif;
  font-weight: 400;
  font-size: 1rem;
}

.button {
  padding: 15px;
  padding-top: 0%;
  padding-bottom: 0%;
  grid-area: addStream-left; 
  height: 44px;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px; /* Adds spacing between the text and the icon */
  margin: 0px;
  padding-top: 3px;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.button:disabled {
  background-color: #23252C;
  color: #4a4d57;
  cursor: not-allowed;
}
</style>
