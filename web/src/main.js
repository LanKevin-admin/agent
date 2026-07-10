import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Config from './views/Config.vue'
import Analysis from './views/Analysis.vue'
import Reports from './views/Reports.vue'
import Chat from './views/Chat.vue'
import Templates from './views/Templates.vue'
import Tasks from './views/Tasks.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { title: '仪表盘' } },
    { path: '/chat', component: Chat, meta: { title: '智能对话' } },
    { path: '/templates', component: Templates, meta: { title: '分析模板' } },
    { path: '/tasks', component: Tasks, meta: { title: '定时任务' } },
    { path: '/analysis', component: Analysis, meta: { title: '日志分析' } },
    { path: '/reports', component: Reports, meta: { title: '历史报告' } },
    { path: '/config', component: Config, meta: { title: '配置管理' } }
  ]
})

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
