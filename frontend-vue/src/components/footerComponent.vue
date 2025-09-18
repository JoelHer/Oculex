<script setup>
import { ref } from 'vue'

defineProps({
    title: String,
    dotcolor: {
        type: String,
        default: '#40F284'
    },
})
</script>

<template>
    <div class="footerComponent">
        <div class="dot" :style="{ backgroundColor: dotcolor }"></div>
        <p>{{ title }}</p>
    </div>
</template>

<style scoped>
.footerComponent {
    padding-left: 10px;
    display: flex;
    align-items: center;
    background-color: #23252c;
    color: #fff;
}
.footerComponent p {
    margin: 0;
    font-family: "Sofia Sans", sans-serif;
    font-weight: 400;
    font-size: 0.8rem;
}
.dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 5px;
    transition: background-color 0.2s ease;
}
</style>
