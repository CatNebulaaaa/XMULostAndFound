// main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 如果你有路由（比如有首页和发布页跳转）

// 1. 正确导入Element Plus和样式（注意大小写！ElementPlus是大写P）
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 2. 创建App实例
const app = createApp(App)

// 3. 注册Element Plus（必须在mount之前）
app.use(ElementPlus)
// 如果有路由，注册路由
if (router) {
    app.use(router)
}

// 4. 挂载到页面
app.mount('#app')