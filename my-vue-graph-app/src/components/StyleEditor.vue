<template>
  <div class="style-editor" :style="positionStyle" v-if="visible" @mousedown.stop>
    <div class="editor-header" @mousedown="initDrag">
      <h4>编辑: {{ targetName }}</h4>
      <button @click="$emit('close')" class="close-btn">&times;</button>
    </div>
    <div class="editor-content">
      <div class="style-group"><label>颜色</label><input type="color" :value="config.color" @input="updateStyle('color', $event.target.value)"></div>
      <div class="style-group" v-if="targetType === 'nodes'"><label>大小 <span>{{ config.size }}</span></label><input type="range" :value="config.size" @input="updateStyle('size', parseFloat($event.target.value))" min="10" max="80" step="1"></div>
      <div class="style-group" v-if="targetType === 'edges'"><label>粗细 <span>{{ config.width }}</span></label><input type="range" :value="config.width" @input="updateStyle('width', parseFloat($event.target.value))" min="0.5" max="10" step="0.5"></div>
      <div class="style-group"><label>标注内容</label><select :value="config.labelProp" @change="updateStyle('labelProp', $event.target.value)"><option v-if="targetType === 'edges'" value="none">无</option><option v-for="prop in availableProps" :key="prop" :value="prop">{{ prop }}</option></select></div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue';
const props = defineProps({ visible: Boolean, position: Object, targetType: String, targetName: String, config: Object, availableProps: Array });
const emit = defineEmits(['close', 'update-style', 'update-position']);
const positionStyle = computed(() => ({ top: `${props.position.top}px`, left: `${props.position.left}px` }));
function updateStyle(key, value) { emit('update-style', { key, value }); }
function initDrag(e) {
  const startX = e.clientX, startY = e.clientY, startTop = props.position.top, startLeft = props.position.left;
  function doDrag(e) { emit('update-position', { top: startTop + e.clientY - startY, left: startLeft + e.clientX - startX }); }
  function stopDrag() { window.removeEventListener('mousemove', doDrag); window.removeEventListener('mouseup', stopDrag); }
  window.addEventListener('mousemove', doDrag);
  window.addEventListener('mouseup', stopDrag);
}
</script>
<style scoped>
.style-editor { position: absolute; z-index: 1000; width: 280px; background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3); color: var(--text-primary); }
.editor-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; border-bottom: 1px solid var(--border-color); cursor: move; }
.editor-header h4 { margin: 0; font-size: 1em; color: var(--text-secondary); }
.close-btn { background: none; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; padding: 0; line-height: 1; }
.editor-content { padding: 15px; }
.style-group { margin-bottom: 15px; }
.style-group label { display: flex; justify-content: space-between; font-weight: 500; margin-bottom: 5px; font-size: 0.9em; }
.style-group select, .style-group input { width: 100%; padding: 8px; background-color: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 4px; }
.style-group input[type="color"] { padding: 2px; height: 38px; }
.style-group input[type="range"] { width: 100%; padding: 0; }
</style>
