<script setup>
import { ref } from 'vue'

const count = ref(0)
</script>

<template>
  <div class="container navbarContainer">        
    <button @click="count++">You clicked me {{ count }} times.</button>
  </div>
</template>

<style scoped>
.container {
  width: calc( 100% - 4px );
  min-height: 45px;
  background-color: #23252c;
  border-radius: 15px;
  border: #2d2f37 solid 2px;
}

.navbarContainer {
  display: grid; 
  grid-template-rows: auto 1fr; /* Let header row size dynamically */
  grid-template-areas: 
  "navbarContainer-header"
  "navbarContainer-body"; 
}
</style>