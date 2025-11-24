<template>
  <!-- 顶部导航栏 -->
  <div style="background: #1989fa; padding: 0 20px;">
    <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; height: 60px;">
      <!-- 标题 -->
      <a href="/" style="color: white; font-size: 20px; font-weight: bold; text-decoration: none;">
        失物招领平台
      </a>
      <!-- 导航链接 -->
      <div style="display: flex; gap: 30px;">
        <a href="/" style="color: white; font-size: 16px; text-decoration: none;">首页</a>
        <router-link to="/upload" style="color: white; font-size: 16px; text-decoration: none; font-weight: 500;">发布失物</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
// 无需额外代码，抄就行
</script>

<style scoped>
/* 导航栏样式，不用改 */
a:hover {
  text-decoration: underline;
}
</style>