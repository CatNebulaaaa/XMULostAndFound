<template>
  <div id="app">
    <div class="app-container">
      <!-- 头部导航栏 -->
      <header class="header">
        <div class="header-content">
          <div class="logo">
            <i class="el-icon-search logo-icon"></i>
            <span>智能物品搜索</span>
          </div>
          <div class="nav-links">
            <router-link to="/search" class="nav-link" :class="{ active: $route.path === '/search' }">
              搜索
            </router-link>
            <router-link to="/upload" class="nav-link" :class="{ active: $route.path === '/upload' }">
              上传
            </router-link>
            <router-link to="/about" class="nav-link" :class="{ active: $route.path === '/about' }">
              关于
            </router-link>
          </div>
        </div>
      </header>

      <!-- 主要内容区域 -->
      <main class="main-content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.logo-icon {
  margin-right: 8px;
  font-size: 24px;
}

.nav-links {
  display: flex;
  gap: 30px;
}

.nav-link {
  color: #606266;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s;
}

.nav-link:hover,
.nav-link.active {
  color: #409eff;
}

.main-content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>