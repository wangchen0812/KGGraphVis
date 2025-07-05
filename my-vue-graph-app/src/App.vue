<!-- src/App.vue -->
<template>
  <div id="app-container">
    <aside class="sidebar">
      <div class="sidebar-section">
        <div class="resizable-textarea">
          <textarea v-model="cypherQuery" @keyup.enter="runQuery" placeholder="输入Cypher查询并按Enter"></textarea>
          <div class="resizer" @mousedown="initResize"></div>
        </div>
        <button @click="runQuery" :disabled="isLoading">
          {{ isLoading ? '查询中...' : '执行查询' }}
        </button>
      </div>
      <div class="overview-list">
        <div v-if="!isLoading && overview.nodes.size > 0">
          <div class="overview-group-header" @click="toggleCollapse('nodes')">
            <ChevronRight class="icon" :class="{ collapsed: collapsedSections.nodes }" :size="18" />
            节点 ({{ rawData.nodes.length }})
          </div>
          <div v-show="!collapsedSections.nodes">
            <div v-for="[category, items] in overview.nodes" :key="category" class="overview-item" :class="{ active: editor.targetName === category }" @click="showEditor('nodes', category, $event)">
              {{ category }} ({{ items.length }})
            </div>
          </div>
        </div>
        <div v-if="!isLoading && overview.edges.size > 0">
          <div class="overview-group-header" @click="toggleCollapse('edges')">
            <ChevronRight class="icon" :class="{ collapsed: collapsedSections.edges }" :size="18" />
            关系 ({{ rawData.links.length }})
          </div>
          <div v-show="!collapsedSections.edges">
            <div v-for="[type, items] in overview.edges" :key="type" class="overview-item" :class="{ active: editor.targetName === type }" @click="showEditor('edges', type, $event)">
              {{ type }} ({{ items.length }})
            </div>
          </div>
        </div>
      </div>
      <div class="sidebar-section">
        <h4>布局设置</h4>
        <div class="style-group">
          <label>节点距离 (斥力) <span>{{ layoutConfig.repulsion }}</span></label>
          <input type="range" v-model.number="layoutConfig.repulsion" min="50" max="500" step="10">
        </div>
        <div class="style-group">
          <label>边长 <span>{{ layoutConfig.edgeLength }}</span></label>
          <input type="range" v-model.number="layoutConfig.edgeLength" min="50" max="300" step="10">
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="main-header">
        <div class="title">知识图谱可视化</div>
        <div class="tabs">
          <div class="tab" :class="{ active: currentView === 'graph' }" @click="currentView = 'graph'">Graph</div>
          <div class="tab" :class="{ active: currentView === 'table' }" @click="currentView = 'table'">Table</div>
        </div>
        <div class="header-controls">
          <button class="control-btn" @click="forceLabelShow = 'on'" title="强制显示所有标签"><MessageSquareText :size="18"/></button>
          <button class="control-btn" @click="forceLabelShow = 'off'" title="强制隐藏所有标签"><MessageSquareOff :size="18"/></button>
          <!-- 【核心修正】使用正确的图标名称 Pointer -->
          <button class="control-btn" @click="forceLabelShow = 'auto'" title="自动显隐标签"><Pointer :size="18"/></button>
          <div class="theme-toggle" @click="toggleTheme"><Sun v-if="theme === 'dark'" :size="20" /> <Moon v-else :size="20" /></div>
        </div>
      </header>
      <div v-if="!isLoading && currentView === 'graph'" class="graph-wrapper">
        <GraphChart
            :graph-data="filteredData"
            :style-config="styleConfig"
            :layout-config="layoutConfig"
            :force-label-show="forceLabelShow"
            :key="chartKey"
            @legend-select-changed="handleLegendChange"
        />
      </div>
      <div v-if="!isLoading && currentView === 'table'" class="table-view">
        <TableView :table-data="tableData" />
      </div>
      <div v-if="isLoading" class="loading-overlay">
        <p>加载中...</p>
      </div>
    </main>

    <StyleEditor
        :visible="editor.visible"
        :position="editor.position"
        :target-type="editor.targetType"
        :target-name="editor.targetName"
        :config="activeEditorConfig"
        :available-props="availableLabelProps"
        @close="editor.visible = false"
        @update-style="handleStyleUpdate"
        @update-position="handleEditorMove"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
// 【核心修正】导入正确的图标名称 Pointer
import { Sun, Moon, ChevronRight, MessageSquareText, MessageSquareOff, Pointer } from 'lucide-vue-next';
import GraphChart from './components/GraphChart.vue';
import TableView from './components/TableView.vue';
import StyleEditor from './components/StyleEditor.vue';

// --- STATE MANAGEMENT ---
const cypherQuery = ref('MATCH p=(n)-[r]->(m) RETURN p LIMIT 10');
const rawData = reactive({ nodes: [], links: [] });
const tableData = reactive({ headers: [], rows: [] });
const currentView = ref('graph');
const theme = ref('dark');
const chartKey = ref(0);
const collapsedSections = reactive({ nodes: false, edges: false });
const editor = reactive({ visible: false, position: { top: 0, left: 0 }, targetType: null, targetName: null });
const styleConfig = reactive({ nodes: {}, edges: {} });
const layoutConfig = reactive({ repulsion: 200, edgeLength: 150 });
const forceLabelShow = ref('auto');
const isLoading = ref(true);

// --- API & DATA HANDLING ---
async function runQuery() {
  isLoading.value = true;
  editor.visible = false;
  // try {
  //   const response = await fetch('http://localhost:5001/graph', {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ cypher: cypherQuery.value }),
  //   });
  try {
    // 【核心修改】使用环境变量,支持线上发布
    const apiUrl = import.meta.env.VITE_API_URL;
    const response = await fetch(`${apiUrl}/graph`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cypher: cypherQuery.value }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const result = await response.json();
    if (result.error) throw new Error(result.error);

    if (result.type === 'graph') {
      rawData.nodes = result.data.nodes || [];
      rawData.links = result.data.links || [];
      tableData.headers = []; tableData.rows = [];
      initializeStyleConfig();
      currentView.value = 'graph';
    } else {
      tableData.headers = result.data.headers || [];
      tableData.rows = result.data.rows || [];
      rawData.nodes = []; rawData.links = [];
      currentView.value = 'table';
    }
  } catch (e) {
    console.error("查询或处理数据时出错:", e);
    alert(`查询失败: ${e.message}`);
  } finally {
    isLoading.value = false;
    chartKey.value++;
  }
}

function initializeStyleConfig() {
  const nodeCategories = [...new Set(rawData.nodes.map(n => n.category))];
  const edgeTypes = [...new Set(rawData.links.map(l => l.name))];
  const defaultColors = ['#8be9fd', '#50fa7b', '#ffb86c', '#ff79c6', '#bd93f9', '#ff6e6e', '#f1fa8c'];

  const newNodesConfig = {};
  nodeCategories.forEach((cat, i) => {
    newNodesConfig[cat] = { visible: true, color: defaultColors[i % defaultColors.length], size: 40, labelProp: 'name', labelFormatter: (n) => n.name };
  });
  styleConfig.nodes = newNodesConfig;

  const newEdgesConfig = {};
  edgeTypes.forEach((type) => {
    const sampleLink = rawData.links.find(l => l.name === type);
    let defaultLabelProp = 'type';
    if (sampleLink?.properties?.event) { defaultLabelProp = 'event'; }
    else if (sampleLink?.properties?.detail) { defaultLabelProp = 'detail'; }
    newEdgesConfig[type] = { visible: true, color: '#6272a4', width: 1.5, labelProp: defaultLabelProp, labelFormatter: (l) => l.properties[defaultLabelProp] || l.properties.type };
  });
  styleConfig.edges = newEdgesConfig;
}

// --- UI INTERACTION HANDLERS ---
function showEditor(type, name, event) {
  const rect = event.currentTarget.getBoundingClientRect();
  editor.targetType = type;
  editor.targetName = name;
  editor.position = { top: rect.top, left: rect.right + 10 };
  editor.visible = true;
}

function handleStyleUpdate({ key, value }) {
  if (!editor.targetName) return;
  const config = styleConfig[editor.targetType]?.[editor.targetName];
  if (config) {
    config[key] = value;
    if (key === 'labelProp') {
      if (editor.targetType === 'nodes') {
        config.labelFormatter = (node) => node.properties[value] || node[value] || '';
      } else {
        config.labelFormatter = (link) => (value === 'none') ? '' : link.properties[value] || '';
      }
    }
  }
}

function handleEditorMove(newPosition) {
  editor.position.top = newPosition.top;
  editor.position.left = newPosition.left;
}

function handleLegendChange(selected) {
  Object.keys(selected).forEach(categoryName => {
    if (styleConfig.nodes[categoryName]) {
      styleConfig.nodes[categoryName].visible = selected[categoryName];
    }
  });
}

// --- COMPUTED PROPERTIES ---
const overview = computed(() => {
  const nodes = new Map();
  if (rawData.nodes) {
    rawData.nodes.forEach(n => { if (!nodes.has(n.category)) nodes.set(n.category, []); nodes.get(n.category).push(n); });
  }
  const edges = new Map();
  if (rawData.links) {
    rawData.links.forEach(l => { if (!edges.has(l.name)) edges.set(l.name, []); edges.get(l.name).push(l); });
  }
  return { nodes, edges };
});

const activeEditorConfig = computed(() => {
  if (!editor.targetName || !styleConfig[editor.targetType] || !styleConfig[editor.targetType][editor.targetName]) {
    return {};
  }
  return styleConfig[editor.targetType][editor.targetName];
});

const availableLabelProps = computed(() => {
  if (!editor.targetName) return [];
  const { targetType, targetName } = editor;
  if (targetType === 'nodes') {
    const sampleNode = rawData.nodes?.find(n => n.category === targetName);
    if (!sampleNode) return ['name', 'id', 'category'];
    return [...new Set(['name', 'id', 'category', ...Object.keys(sampleNode.properties || {})])];
  } else {
    const sampleLink = rawData.links?.find(l => l.name === targetName);
    if (!sampleLink) return ['type'];
    return [...new Set(['type', ...Object.keys(sampleLink.properties || {})])];
  }
});

const filteredData = computed(() => {
  if (!styleConfig.nodes || Object.keys(styleConfig.nodes).length === 0) {
    return { nodes: [], links: [] };
  }
  const visibleNodeCategories = Object.keys(styleConfig.nodes).filter(cat => styleConfig.nodes[cat]?.visible);
  const nodes = rawData.nodes.filter(n => visibleNodeCategories.includes(n.category));
  const nodeIds = new Set(nodes.map(n => n.id));
  const links = rawData.links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
  return { nodes, links };
});

// --- HELPERS & LIFECYCLE ---
function initResize(e) {
  const textarea = e.target.previousElementSibling;
  const startY = e.clientY, startHeight = parseInt(document.defaultView.getComputedStyle(textarea).height, 10);
  function doDrag(e) { textarea.style.height = (startHeight + e.clientY - startY) + 'px'; }
  function stopDrag() { window.removeEventListener('mousemove', doDrag); window.removeEventListener('mouseup', stopDrag); }
  window.addEventListener('mousemove', doDrag);
  window.addEventListener('mouseup', stopDrag);
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
  document.body.className = theme.value + '-theme';
  chartKey.value++;
}

function toggleCollapse(section) {
  collapsedSections[section] = !collapsedSections[section];
}

onMounted(() => {
  document.body.className = theme.value + '-theme';
  runQuery();
});
</script>

<style scoped>
.loading-overlay {
  width: 100%; height: 100%; display: flex; justify-content: center;
  align-items: center; font-size: 1.5rem; color: var(--text-muted);
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.main-header .header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}
.main-header .control-btn {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, border-color 0.2s;
}
.main-header .control-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-primary);
}
.main-header .theme-toggle {
  cursor: pointer;
  color: var(--text-primary);
  display: flex;
  align-items: center;
}
</style>
