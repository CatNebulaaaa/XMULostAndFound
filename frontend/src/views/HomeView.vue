<!-- frontend/src/views/HomeView.vue -->
<template>
  <div class="home-container">
    
    <!-- 1. 蓝色 Banner 区域 -->
    <div class="banner-section">
      <h1 class="main-title">🔎 XMU 校园失物招领中心</h1>
      
      <!-- 搜索框卡片 -->
      <div class="search-box-card">
        <el-input
          v-model="searchText"
          placeholder="输入关键词（如：黑色书包）..."
          size="large"
          class="custom-search-input"
          @keyup.enter="performSearch"
        >
          <template #suffix>
            <div class="search-actions">
              <!-- 图片上传组件 -->
              <el-upload
                ref="uploadRef" 
                :auto-upload="false"
                :show-file-list="false"
                @change="handleImageSearch"
                accept="image/*"
                class="upload-icon-btn"
              >
                <!-- 根据状态显示不同文字 -->
                <el-button link :type="searchImagePreview ? 'success' : 'default'">
                  <el-icon><Camera /></el-icon> {{ searchImagePreview ? '已选图 (点击更换)' : '以图搜图' }}
                </el-button>
              </el-upload>
              
              <el-button type="primary" @click="performSearch" :loading="loading">搜索</el-button>
            </div>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 2. 内容区域：标签页切换 -->
    <div class="content-section">
      <el-tabs v-model="activeTab" class="custom-tabs">
        
        <!-- Tab 1: 招领 -->
        <el-tab-pane label="👀 最近捡到的 (招领)" name="found">
          <div class="items-grid" v-loading="loading">
             <div v-if="foundItems?.length === 0" class="empty-state">
                <el-empty description="暂无招领信息，大家保管得很好！" />
             </div>
             
             <el-row :gutter="20" v-else>
               <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in foundItems" :key="item.id">
                 <el-card shadow="hover" class="item-card" :body-style="{ padding: '0px' }">
                    <div class="image-wrapper">
                      <el-image 
                        :src="getImageUrl(item.image_filename)" 
                        fit="cover" 
                        class="card-image"
                        lazy
                      >
                        <template #error>
                          <div class="image-error">
                            <el-icon><Picture /></el-icon>
                          </div>
                        </template>
                      </el-image>
                      <div class="category-tag">{{ item.category }}</div>
                    </div>
                    <div class="card-content">
                      <div class="card-header-row">
                        <h3 class="item-desc">{{ item.description }}</h3>
                      </div>
                      <div class="info-row">
                        <el-icon><Location /></el-icon>
                        <span class="location-text">{{ item.location }}</span>
                      </div>
                      <div class="info-row contact-row" v-if="item.contact">
                        <el-icon><Phone /></el-icon>
                        <span class="contact-text">{{ item.contact }}</span>
                      </div>
                      <div class="time-row">
                        {{ formatDate(item.timestamp) }}
                      </div>
                    </div>
                 </el-card>
               </el-col>
             </el-row>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 寻物 -->
        <el-tab-pane label="📢 最近丢失的 (寻物)" name="lost">
          <div class="items-grid" v-loading="loading">
            <div v-if="lostItems?.length === 0" class="empty-state">
                <el-empty description="暂无寻物启事，天下无贼！" />
             </div>
             <el-row :gutter="20" v-else>
               <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in lostItems" :key="item.id">
                 <el-card shadow="hover" class="item-card" :body-style="{ padding: '0px' }">
                    <div class="image-wrapper">
                      <el-image 
                        :src="getImageUrl(item.image_filename)" 
                        fit="cover" 
                        class="card-image"
                        lazy
                      >
                        <template #error>
                          <div class="image-error">
                            <el-icon><Picture /></el-icon>
                          </div>
                        </template>
                      </el-image>
                      <div class="category-tag">{{ item.category }}</div>
                    </div>
                    <div class="card-content">
                      <div class="card-header-row">
                        <h3 class="item-desc">{{ item.description }}</h3>
                      </div>
                      <div class="info-row">
                        <el-icon><Location /></el-icon>
                        <span class="location-text">{{ item.location }}</span>
                      </div>
                      <div class="info-row contact-row" v-if="item.contact">
                        <el-icon><Phone /></el-icon>
                        <span class="contact-text">{{ item.contact }}</span>
                      </div>
                      <div class="time-row">
                        {{ formatDate(item.timestamp) }}
                      </div>
                    </div>
                 </el-card>
               </el-col>
             </el-row>
          </div>
        </el-tab-pane>

      </el-tabs>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Camera, Location, Picture, Phone } from '@element-plus/icons-vue';
import apiClient from '../api';

// 后端地址
const API_BASE_URL = 'https://catnebulaaa-xmulostandfound.hf.space';

const searchText = ref('');
const activeTab = ref('found'); 
const loading = ref(false);
const allItems = ref([]); 
const searchImageFile = ref(null);
const searchImagePreview = ref(false);
const uploadRef = ref(null); // 绑定到 el-upload 组件

const foundItems = computed(() => {
  if (!allItems.value) return [];
  return allItems.value.filter(item => item.item_type === 'found');
});

const lostItems = computed(() => {
  if (!allItems.value) return [];
  return allItems.value.filter(item => item.item_type === 'lost');
});

const fetchAllItems = async () => {
  loading.value = true;
  try {
    const res = await apiClient.get('/api/items');
    allItems.value = res.data.results || [];
  } catch (err) {
    console.error("获取数据失败:", err);
    allItems.value = [];
  } finally {
    loading.value = false;
  }
};

// 核心修改：清除搜索图片的函数
const clearSearchImage = () => {
  searchImageFile.value = null;      // 清空文件变量
  searchImagePreview.value = false;  // 重置预览状态
  if (uploadRef.value) {
    uploadRef.value.clearFiles();    // 清空 Element Plus 组件内部的文件列表
  }
};

const performSearch = async () => {
  loading.value = true;
  const formData = new FormData();
  if (searchText.value) formData.append('query_text', searchText.value);
  if (searchImageFile.value) formData.append('query_image', searchImageFile.value);

  try {
    const res = await apiClient.post('/api/search', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    allItems.value = res.data.results || [];
  } catch (err) {
    console.error(err);
    // 这里不清空 allItems，保留上次结果或显示错误提示可能更好，看需求
  } finally {
    loading.value = false;
    // 核心修改：搜索结束后自动清空选中的图片
    clearSearchImage();
  }
};

const handleImageSearch = (file) => {
  searchImageFile.value = file.raw;
  searchImagePreview.value = true;
};

const getImageUrl = (filename) => {
  if (!filename) return '';
  if (filename.startsWith('http')) return filename;
  return `${API_BASE_URL}/api/images/${filename}`;
};

const formatDate = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

onMounted(() => {
  fetchAllItems();
});
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

/* 蓝色 Banner */
.banner-section {
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
  padding: 60px 20px 100px;
  text-align: center;
  position: relative;
}

.main-title {
  color: #2c3e50;
  font-size: 32px;
  margin-bottom: 40px;
  text-shadow: 0 2px 4px rgba(255,255,255,0.5);
}

/* 悬浮搜索框 */
.search-box-card {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  padding: 10px;
  border-radius: 50px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
}

.custom-search-input :deep(.el-input__wrapper) {
  box-shadow: none;
}

.search-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 内容区域 */
.content-section {
  max-width: 1200px;
  margin: -60px auto 0;
  padding: 0 20px;
  position: relative;
  z-index: 10;
}

.custom-tabs {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  min-height: 400px;
}

.empty-state {
  padding: 50px 0;
}

/* 卡片样式 */
.item-card {
  margin-bottom: 20px;
  border: none;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.item-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 200px;
  background-color: #f5f7fa;
}

.card-image {
  width: 100%;
  height: 100%;
  display: block;
}

.image-error {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #c0c4cc;
  font-size: 30px;
}

.category-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.card-content {
  padding: 14px;
}

.item-desc {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-row {
  display: flex;
  align-items: center;
  color: #606266;
  font-size: 13px;
  margin-bottom: 6px;
  gap: 5px;
}

.contact-row {
  color: #409eff;
}

.time-row {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
  text-align: right;
  border-top: 1px solid #ebeef5;
  padding-top: 10px;
}
</style>