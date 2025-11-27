<template>
  <div class="app-layout">
    <Header />
    <!-- 关键：这里显示当前路由匹配到的页面 -->
    <router-view />
  </div>
</template>

<script setup>
// 确保路径对，Components 首字母大写
import Header from './components/Header.vue'
</script>

<style>
body { margin: 0; font-family: sans-serif; }
.app-layout { max-width: 1200px; margin: 0 auto; padding: 20px; }
</style>