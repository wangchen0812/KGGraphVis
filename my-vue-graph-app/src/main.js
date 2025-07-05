import { createApp } from 'vue'
import App from './App.vue'

// 【核心修正】在这里引入全局样式文件，确保它最先被应用
import './style.css'

createApp(App).mount('#app')
