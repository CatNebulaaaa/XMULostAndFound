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
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                @change="handleImageSearch"
                accept="image/*"
                class="upload-icon-btn"
              >
                <el-button link>
                  <el-icon><Camera /></el-icon> {{ searchImagePreview ? '已选图' : '以图搜图' }}
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
        <el-tab-pane label="👀 最近捡到的 (招领)" name="found">
          <div class="items-grid" v-loading="loading">
             <div v-if="foundItems.length === 0" class="empty-state">
                <el-empty description="暂无招领信息，大家保管得很好！" />
             </div>
             <el-row :gutter="20" v-else>
               <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in foundItems" :key="item.id">
                 <ItemCard :item="item" />
               </el-col>
             </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane label="📢 最近丢失的 (寻物)" name="lost">
          <div class="items-grid" v-loading="loading">
            <div v-if="lostItems.length === 0" class="empty-state">
                <el-empty description="暂无寻物启事，天下无贼！" />
             </div>
             <el-row :gutter="20" v-else>
               <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in lostItems" :key="item.id">
                 <ItemCard :item="item" />
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
import { Camera } from '@element-plus/icons-vue';
import apiClient from '../api';
// 假设你有一个子组件展示卡片，如果没有，可以把下面的 ItemCard 换成你之前的卡片 HTML
import ItemGrid from '../components/ItemGrid.vue'; // 或者你之前的卡片代码

const searchText = ref('');
const activeTab = ref('found');
const loading = ref(false);
const allItems = ref([]);
const searchImageFile = ref(null);
const searchImagePreview = ref(false);

// 过滤数据：根据 Tab 分类
const foundItems = computed(() => allItems.value.filter(item => item.item_type === 'found'));
const lostItems = computed(() => allItems.value.filter(item => item.item_type === 'lost'));

// 一个简单的内部组件用于展示卡片 (如果你没有 ItemGrid.vue，可以直接写在上面)
const ItemCard = ItemGrid; 

const fetchAllItems = async () => {
  loading.value = true;
  try {
    const res = await apiClient.get('/api/items');
    allItems.value = res.data.results || [];
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
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
  } finally {
    loading.value = false;
  }
};

const handleImageSearch = (file) => {
  searchImageFile.value = file.raw;
  searchImagePreview.value = true;
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
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); /* 仿截图的淡蓝色渐变 */
  padding: 60px 20px 100px; /* 底部留白给搜索框 */
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
  border-radius: 50px; /* 圆角 */
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
}

.custom-search-input :deep(.el-input__wrapper) {
  box-shadow: none; /* 去掉默认边框 */
}

.search-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 内容区域 */
.content-section {
  max-width: 1200px;
  margin: -60px auto 0; /* 向上重叠 Banner */
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
</style>