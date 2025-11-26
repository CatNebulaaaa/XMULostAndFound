<template>
  <div class="header-wrapper">
    <div class="logo-area" @click="$router.push('/')">
      <span class="logo-icon">🏫</span>
      <span class="logo-text">XMU 失物招领</span>
    </div>
    <div class="nav-links">
      <router-link to="/" class="nav-item" active-class="active">
        <el-icon><Search /></el-icon> 搜索/广场
      </router-link>
      <router-link to="/upload" class="nav-item" active-class="active">
        <el-icon><CirclePlus /></el-icon> 发布信息
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { Search, CirclePlus } from '@element-plus/icons-vue'
</script>

<style scoped>
.header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-bottom: 20px;
  border-radius: 8px;
}

.logo-area {
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  color: #3a6073;
}

.logo-icon {
  margin-right: 10px;
  font-size: 24px;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-item {
  text-decoration: none;
  color: #666;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  border-radius: 20px;
  transition: all 0.3s;
}

.nav-item:hover {
  background-color: #f0f2f5;
  color: #3a7bd5;
}

.nav-item.active {
  background-color: #e6f0ff;
  color: #3a7bd5;
  font-weight: bold;
}
</style>