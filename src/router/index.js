// 导入Vue路由工具（不用懂，抄就行）
import { createRouter, createWebHistory } from 'vue-router';

// 导入页面组件
import HomeView from '../views/HomeView.vue'; // 首页（占位）
import UploadView from '../views/UploadView.vue'; // 你的上传页

// 路由规则：访问哪个地址，显示哪个页面
const routes = [
    {
        path: '/', // 网站默认地址（打开就显示）
        name: 'Home',
        component: HomeView
    },
    {
        path: '/upload', // 上传页地址（网站域名+/upload）
        name: 'Upload',
        component: UploadView
    }
];

// 创建路由实例
const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
});

// 导出路由（供App.vue使用）
export default router;