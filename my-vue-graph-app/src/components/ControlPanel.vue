<template>
  <div class="control-panel">
    <!-- Template部分保持完全不变 -->
    <div class="control-section">
      <h3>Cypher 查询</h3>
      <textarea v-model="cypherQuery" placeholder="输入您的Cypher查询语句..."></textarea>
      <button @click="$emit('run-query', cypherQuery)">执行查询</button>
      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
    <div class="control-section" v-if="Object.keys(styleConfig.nodes).length">
      <div class="legend-controls">
        <h3>图例</h3>
        <label><input type="checkbox" :checked="allVisible" @change="toggleAllVisibility"> 全选</label>
      </div>
      <div id="node-legend-list" class="legend-list">
        <div v-for="(config, name) in styleConfig.nodes" :key="name" class="legend-item" :class="{ active: isActive('nodes', name) }" @click="selectItem('nodes', name)">
          <input type="checkbox" :checked="config.visible" @change.stop="$emit('toggle-visibility', { type: 'nodes', name, visible: $event.target.checked })">
          <div class="legend-color-dot" :style="{ backgroundColor: config.color }"></div>
          <span>{{ name }}</span>
        </div>
      </div>
      <div id="edge-legend-list" class="legend-list">
        <div v-for="(config, name) in styleConfig.edges" :key="name" class="legend-item" :class="{ active: isActive('edges', name) }" @click="selectItem('edges', name)">
          <input type="checkbox" :checked="config.visible" @change.stop="$emit('toggle-visibility', { type: 'edges', name, visible: $event.target.checked })">
          <div class="legend-color-dot" :style="{ backgroundColor: config.color }"></div>
          <span>{{ name }}</span>
        </div>
      </div>
    </div>
    <div class="control-section">
      <h3>布局设置</h3>
      <div class="style-group">
        <label>节点斥力 <span>{{ layoutConfig.repulsion }}</span></label>
        <input type="range" :value="layoutConfig.repulsion" @input="$emit('update-layout', { key: 'repulsion', value: $event.target.value })" min="0" max="500">
      </div>
      <div class="style-group">
        <label>边长 <span>{{ layoutConfig.edgeLength }}</span></label>
        <input type="range" :value="layoutConfig.edgeLength" @input="$emit('update-layout', { key: 'edgeLength', value: $event.target.value })" min="20" max="300">
      </div>
    </div>
    <div class="control-section" id="editor-section" v-if="activeEditorTarget">
      <h3>编辑: {{ activeEditorTarget.name }}</h3>
      <div class="style-group">
        <label>颜色</label>
        <input type="color" :value="activeConfig.color" @input="updateStyle('color', $event.target.value)">
      </div>
      <div class="style-group" v-if="activeEditorTarget.type === 'nodes'">
        <label>大小</label>
        <select :value="activeConfig.size" @change="updateStyle('size', parseFloat($event.target.value))">
          <option value="20">小</option><option value="35">中</option><option value="50">大</option>
        </select>
      </div>
      <div class="style-group" v-if="activeEditorTarget.type === 'edges'">
        <label>粗细</label>
        <select :value="activeConfig.width" @change="updateStyle('width', parseFloat($event.target.value))">
          <option value="1">细</option><option value="2">中</option><option value="4">粗</option>
        </select>
      </div>
      <div class="style-group">
        <label>标注内容</label>
        <select :value="activeConfig.labelProp" @change="updateStyle('labelProp', $event.target.value)">
          <option v-if="activeEditorTarget.type === 'edges'" value="none">无</option>
          <option v-for="prop in availableLabelProps" :key="prop" :value="prop">{{ prop }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
// --- JavaScript部分保持完全不变 ---
import { ref, computed } from 'vue';
const props = defineProps({ styleConfig: Object, layoutConfig: Object, activeEditorTarget: Object, availableLabelProps: Array, error: String });
const emit = defineEmits(['run-query', 'toggle-visibility', 'update-layout', 'select-item', 'update-style']);
const cypherQuery = ref('MATCH p=(n)-[r]->(m) RETURN p LIMIT 15');
const allVisible = computed(() => { return [...Object.values(props.styleConfig.nodes), ...Object.values(props.styleConfig.edges)].every(c => c.visible); });
const activeConfig = computed(() => { if (!props.activeEditorTarget) return {}; const { type, name } = props.activeEditorTarget; return props.styleConfig[type][name]; });
function isActive(type, name) { return props.activeEditorTarget?.type === type && props.activeEditorTarget?.name === name; }
function selectItem(type, name) { emit('select-item', { type, name }); }
function updateStyle(key, value) { emit('update-style', { key, value }); }
function toggleAllVisibility(event) {
  const isChecked = event.target.checked;
  Object.keys(props.styleConfig.nodes).forEach(name => emit('toggle-visibility', { type: 'nodes', name, visible: isChecked }));
  Object.keys(props.styleConfig.edges).forEach(name => emit('toggle-visibility', { type: 'edges', name, visible: isChecked }));
}
</script>

<style scoped>
/* 【核心修正】将所有控制面板的样式移到这里，实现组件封装 */
.control-panel {
  width: 350px;
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: 3px 0px 10px rgba(0,0,0,0.2);
  z-index: 100;
}
.control-section { padding: 20px; border-bottom: 1px solid #4a627a; }
.control-section:last-child { border-bottom: none; }
h3 { margin: 0 0 15px 0; font-size: 1.1em; color: #3498db; text-transform: uppercase; letter-spacing: 1px; }
textarea { width: 100%; height: 120px; background-color: #34495e; color: #ecf0f1; border: 1px solid #4a627a; border-radius: 4px; padding: 10px; font-family: 'Courier New', monospace; resize: vertical; margin-bottom: 10px; }
button { background-color: #3498db; color: white; font-weight: bold; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; width: 100%; transition: background-color 0.2s; }
button:hover { background-color: #4aa9e9; }
.error-message { color: #e74c3c; margin-top: 10px; font-size: 0.9em; }
.legend-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.legend-list { max-height: 200px; overflow-y: auto; padding-right: 5px; }
.legend-item { display: flex; align-items: center; margin-bottom: 8px; padding: 5px; border-radius: 4px; cursor: pointer; transition: background-color 0.2s; }
.legend-item:hover, .legend-item.active { background-color: #34495e; }
.legend-item input[type="checkbox"] { margin-right: 10px; }
.legend-color-dot { width: 15px; height: 15px; border-radius: 50%; margin-right: 10px; flex-shrink: 0; }
.legend-item span { flex-grow: 1; }
.style-group { margin-bottom: 15px; }
.style-group label { display: flex; justify-content: space-between; font-weight: 500; margin-bottom: 5px; font-size: 0.9em; }
.style-group select, .style-group input[type="color"] { width: 100%; padding: 8px; background-color: #34495e; color: #ecf0f1; border: 1px solid #4a627a; border-radius: 4px; box-sizing: border-box; }
.style-group input[type="range"] { width: 100%; padding: 0; }
</style>
