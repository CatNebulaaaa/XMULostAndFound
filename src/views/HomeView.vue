<template>
  <div class="home-view">
    <el-card class="search-card">
      <h1 class="title">🔎 XMU 校园失物招领中心</h1>
      
      <el-form @submit.prevent="performSearch" class="search-form">
        <el-input
          v-model="searchText"
          placeholder="请输入物品描述或图片中的文字..."
          size="large"
          clearable
          class="search-input"
        >
          <template #prepend>
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              @change="handleSearchImageChange"
              accept="image/*"
            >
              <el-button type="primary">{{ searchImagePreview ? '已选图' : '以图搜图' }}</el-button>
            </el-upload>
          </template>
          <template #append>
            <el-button @click="performSearch" type="primary" native-type="submit" :loading="loading">搜索</el-button>
          </template>
        </el-input>
      </el-form>

      <div v-if="searchImagePreview" class="image-preview-container">
        <el-image :src="searchImagePreview" fit="contain" class="image-preview" />
        <el-button @click="clearSearchImage" type="danger" link>清除图片</el-button>
      </div>

    </el-card>

    <div class="results-container">
      <div class="results-header">
        <h2>🎯 搜索结果 ({{ results.length }})</h2>
        <el-button v-if="isSearched" @click="fetchAllItems" type="primary" link>返回广场</el-button>
      </div>

      <el-row :gutter="20" v-loading="loading">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in results" :key="item.id" class="result-col">
          <el-card shadow="hover" class="result-card">
            <el-image :src="getImageUrl(item.image_filename)" lazy fit="cover" class="result-image">
              <template #error>
                <div class="image-slot">加载失败</div>
              </template>
            </el-image>
            <div class="result-info">
              <p class="description">{{ item.description }}</p>
              <p class="location"><b>地点:</b> {{ item.location }}</p>
              <p class="category"><b>分类:</b> {{ item.category }}</p>
              <time class="time">{{ new Date(item.timestamp).toLocaleString() }}</time>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!loading && results.length === 0" description="暂无物品信息或未找到匹配结果"></el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import apiClient from '../api'; // 确保 api.js 存在于 src 目录下

const searchText = ref('');
const searchImageFile = ref(null);
const searchImagePreview = ref('');
const results = ref([]);
const loading = ref(false);
const isSearched = ref(false); // 标记是否执行过搜索
const uploadRef = ref(null);

const API_BASE_URL = 'https://catnebulaaa-xmulostandfound.hf.space'; // 你的 Space URL

// 获取完整图片 URL
const getImageUrl = (filename) => {
  if (!filename) return '';
  return `${API_BASE_URL}/api/images/${filename}`;
};

// 获取所有物品（首页加载时）
const fetchAllItems = async () => {
  loading.value = true;
  isSearched.value = false; // 重置搜索标记
  try {
    const response = await apiClient.get('/items');
    results.value = response.data.results || [];
  } catch (error) {
    console.error('获取物品列表失败:', error);
    results.value = [];
  } finally {
    loading.value = false;
  }
};

// 执行搜索
const performSearch = async () => {
  if (!searchText.value && !searchImageFile.value) {
    // 如果搜索条件为空，则刷新为全部物品
    await fetchAllItems();
    return;
  }

  loading.value = true;
  isSearched.value = true;
  const formData = new FormData();
  if (searchText.value) {
    formData.append('query_text', searchText.value);
  }
  if (searchImageFile.value) {
    formData.append('query_image', searchImageFile.value);
  }

  try {
    const response = await apiClient.post('/search', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    results.value = response.data.results || [];
  } catch (error) {
    console.error('搜索失败:', error);
    results.value = [];
  } finally {
    loading.value = false;
  }
};

// 处理图片选择
const handleSearchImageChange = (file) => {
  const rawFile = file.raw;
  if (rawFile) {
    searchImageFile.value = rawFile;
    searchImagePreview.value = URL.createObjectURL(rawFile);
  }
};

// 清除选择的图片
const clearSearchImage = () => {
  searchImageFile.value = null;
  searchImagePreview.value = '';
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
};

// 组件挂载时加载所有物品
onMounted(() => {
  fetchAllItems();
});
</script>

<style scoped>
.home-view {
  width: 100%;
  padding: 20px;
}
.title {
  text-align: center;
  margin-bottom: 20px;
}
.search-card {
  margin-bottom: 30px;
}
.search-form {
  max-width: 800px;
  margin: 0 auto;
}
.image-preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 15px;
}
.image-preview {
  width: 150px;
  height: 150px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  margin-bottom: 5px;
}
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.result-col {
  margin-bottom: 20px;
}
.result-card .result-image {
  width: 100%;
  height: 200px;
  display: block;
}
.result-info {
  padding: 14px;
}
.result-info p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}
.result-info .description {
  font-weight: bold;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-info .time {
  font-size: 12px;
  color: #999;
}
.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
}
</style>