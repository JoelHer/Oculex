<script setup>
import { Icon } from "@iconify/vue";
</script>

<template>
    <div id="streamPreviewAdd">
        <Icon id="plusIcon" icon="mdi:plus" width="87" height="87" />
    </div>
</template>

<style scoped>
#streamPreviewAdd {
    width: 233px; 
    height: 162px;
    flex-shrink: 0;
    border-radius: 15px;
    overflow: hidden;
    position: relative; 
    border: #23252C solid 4px;
    box-sizing: border-box;
    cursor: pointer;
    transition: border-color 0.3s ease;
}

#streamPreviewAdd:hover {
    border-color: #4a4d57;
    transition: border-color 0.3s ease;
}

#streamPreviewAdd:hover #plusIcon {
    width: 90px;
    height: 90px;
    color: #4a4d57;
    transition: width 0.3s ease, height 0.3s ease, color 0.3s ease;
}

#plusIcon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #23252C;
    transition: width 0.3s ease, height 0.3s ease, color 0.3s ease;
}

</style>
