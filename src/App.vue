<template>
  <div id="app">
    <!-- 导航栏组件 -->
    <Header />
    <!-- 路由视图：根据访问地址显示不同页面 -->
    <router-view />
  </div>
</template>

<script setup>
// 导入导航栏组件和路由
import Header from './components/Header.vue';
import router from './router';
</script>

<style scoped>
/* 全局样式：页面背景色+字体 */
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f7fa;
  min-height: 100vh;
}
</style>
