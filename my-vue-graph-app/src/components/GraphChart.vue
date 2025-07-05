<!-- src/components/GraphChart.vue -->
<template>
  <div ref="chartRef" style="width: 100%; height: 100%;"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  graphData: Object,
  styleConfig: Object,
  layoutConfig: Object,
  forceLabelShow: String,
});
const emit = defineEmits(['legend-select-changed']);

const chartRef = ref(null);
let myChart = null;

onMounted(() => {
  myChart = echarts.init(chartRef.value, document.body.className.includes('dark') ? 'dark' : null);
  renderChart();
  window.addEventListener('resize', () => myChart?.resize());
  myChart.on('finished', () => myChart.on('graphroam', updateLabelVisibility));
  myChart.on('legendselectchanged', (params) => emit('legend-select-changed', params.selected));
  myChart.on('dragend', (params) => {
    if (params.target) {
      const option = myChart.getOption();
      option.series[0].data[params.dataIndex].fixed = true;
      myChart.setOption(option);
    }
  });
  myChart.on('dblclick', (params) => {
    if (params.dataType === 'node' && params.data.fixed) {
      const option = myChart.getOption();
      option.series[0].data[params.dataIndex].fixed = false;
      myChart.setOption(option);
    }
  });
});

onUnmounted(() => myChart?.dispose());

watch(() => [props.graphData, props.styleConfig, props.layoutConfig, props.forceLabelShow], renderChart, { deep: true });
watch(() => document.body.className, () => {
  myChart?.dispose();
  myChart = echarts.init(chartRef.value, document.body.className.includes('dark') ? 'dark' : null);
  renderChart();
});

function updateLabelVisibility() {
  if (!myChart) return;
  const option = myChart.getOption();
  if (!option || !option.series || !option.series.length) return;
  let showLabel;
  if (props.forceLabelShow === 'on') { showLabel = true; }
  else if (props.forceLabelShow === 'off') { showLabel = false; }
  else { const zoom = option.series[0].zoom; showLabel = zoom > 0.7; }
  myChart.setOption({ series: [{ label: { show: showLabel }, edgeLabel: { show: showLabel } }] });
}

function renderChart() {
  // 【核心修复】添加防御性编程，确保所有必要数据都已准备好
  if (!myChart || !props.graphData || !props.graphData.nodes || props.graphData.nodes.length === 0 || !props.styleConfig.nodes || Object.keys(props.styleConfig.nodes).length === 0) {
    myChart.clear(); // 如果数据不完整，清空图表
    return;
  }

  const nodes = props.graphData.nodes.map(node => {
    const style = props.styleConfig.nodes[node.category] || {};
    const labelFormatter = style.labelFormatter || ((n) => n.name);
    return { ...node, symbolSize: style.size || 35, itemStyle: { color: style.color }, label: { formatter: labelFormatter(node) } };
  });

  const links = props.graphData.links.map(link => {
    const style = props.styleConfig.edges[link.name] || {};
    const labelFormatter = style.labelFormatter || ((l) => l.name);
    return { ...link, lineStyle: { color: style.color, width: style.width }, label: { formatter: labelFormatter(link) } };
  });

  const categories = Object.keys(props.styleConfig.nodes).map(name => ({ name, itemStyle: { color: props.styleConfig.nodes[name].color } }));
  const legendSelected = {};
  Object.entries(props.styleConfig.nodes).forEach(([name, config]) => { legendSelected[name] = config.visible; });

  myChart.setOption({
    tooltip: {
      formatter: (params) => {
        if (params.dataType === 'node') return `<b>${params.data.name}</b> (${params.data.category})`;
        if (params.dataType === 'edge') {
          const source = props.graphData.nodes.find(n => n.id === params.data.source)?.name || '未知';
          const target = props.graphData.nodes.find(n => n.id === params.data.target)?.name || '未知';
          return `${source} -[${params.data.name}]-> ${target}`;
        }
      }
    },
    legend: { show: true, top: '20px', left: '20px', orient: 'vertical', data: categories.map(c => c.name), selected: legendSelected, textStyle: { color: 'auto' } },
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      data: nodes, links: links, categories: categories,
      label: { show: false, position: 'inside', color: '#fff', fontSize: 12, textShadowBlur: 2, textShadowColor: 'rgba(0, 0, 0, 0.5)' },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: [4, 10],
      edgeLabel: { show: false, position: 'middle', fontSize: 10, color: 'auto' },
      lineStyle: { opacity: 0.8, curveness: 0.1 },
      force: { repulsion: props.layoutConfig.repulsion, edgeLength: props.layoutConfig.edgeLength, gravity: 0.1, friction: 0.6, layoutAnimation: true },
      itemStyle: { borderWidth: 1.5, borderColor: 'rgba(255,255,255,0.3)', shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' },
      emphasis: { focus: 'adjacency', lineStyle: { width: 4 } }
    }]
  }, { notMerge: true });
  setTimeout(updateLabelVisibility, 100);
}
</script>
