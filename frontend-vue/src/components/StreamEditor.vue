<script setup>
import { ref } from 'vue'

defineProps({
  streamId: String
})

const count = ref(0)
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
                    <h1>Editing Stream: {{ streamId }}</h1>
                </div>
                <div class="navbarContainer-body">

                </div>
            </div>
        </div>
        <div class="editorView">
            <h1>{{ msg }}</h1>
            <button type="button" @click="count++">count is {{ count }}</button>
        </div>
    </div>
</template>

<style scoped>
.streamEditor {  
    display: grid;
    height: 100%;
    width: 100%;
    grid-template-columns: 300px 1fr;
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
    border-radius: 18px;
    border: #2d2f37 solid 3px;
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
    grid-auto-columns: 1fr; 
    grid-template-columns: 1fr; 
    grid-template-rows: 100px 1fr; 
    gap: 0px 0px; 
    grid-template-areas: 
        "navbarContainer-header"
        "navbarContainer-body"; 
}

.navbarContainer-header { 
    grid-area: navbarContainer-header; 
}
.navbarContainer-body { 
    grid-area: navbarContainer-body; 
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
}

</style>
