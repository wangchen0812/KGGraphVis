<!-- src/components/TableView.vue -->
<template>
  <div v-if="tableData.rows.length > 0">
    <table>
      <thead>
      <tr>
        <th v-for="header in tableData.headers" :key="header">{{ header }}</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(row, index) in tableData.rows" :key="index">
        <td v-for="header in tableData.headers" :key="header">{{ row[header] }}</td>
      </tr>
      </tbody>
    </table>
  </div>
  <div v-else>
    <p>没有表格数据可显示。</p>
  </div>
</template>

<script setup>
defineProps({ tableData: Object });
</script>
