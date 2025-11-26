<template>
  <div class="home-container">
    <!-- 1. Hero 搜索区 (保持之前的样式，略微调整) -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="main-title">🔎 XMU 校园失物招领中心</h1>
        
        <el-card class="search-card" shadow="always">
          <div class="search-box">
            <el-input 
              v-model="queryText" 
              placeholder="输入关键词（如：黑色书包）..." 
              class="search-input" size="large" clearable @keyup.enter="doSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            
            <input type="file" ref="fileInput" @change="handleImageSearch" accept="image/*" style="display: none" />
            
            <el-button @click="$refs.fileInput.click()" size="large" :type="searchImage ? 'success' : 'default'">
              <el-icon><Camera /></el-icon> {{ searchImage ? '已选图' : '以图搜图' }}
            </el-button>
            
            <el-button type="primary" size="large" @click="doSearch">搜索</el-button>
          </div>
          <!-- 预览图 -->
          <div v-if="previewUrl" class="img-preview-box">
             <img :src="previewUrl" />
             <el-link type="danger" @click="clearImage">清除图片</el-link>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 2. 信息展示广场 (新功能) -->
    <div class="plaza-section">
      <!-- 如果是搜索结果模式 -->
      <div v-if="isSearching" class="results-wrapper">
        <div class="section-title">
            <h3>🎯 搜索结果 ({{ results.length }})</h3>
            <el-button link @click="resetSearch">返回广场</el-button>
        </div>
        <ItemGrid :items="results" />
      </div>

      <!-- 如果是默认广场模式 -->
      <div v-else class="tabs-wrapper">
        <el-tabs v-model="activeTab" class="custom-tabs" @tab-click="fetchInitialData">
          <el-tab-pane label="👀 最近捡到的 (招领)" name="found">
            <ItemGrid :items="foundItems" empty-text="暂无招领信息，大家都保管得很好！" />
          </el-tab-pane>
          <el-tab-pane label="📢 最近丢失的 (寻物)" name="lost">
             <ItemGrid :items="lostItems" empty-text="暂无寻物信息，希望大家都没丢东西！" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Search, Camera } from '@element-plus/icons-vue'
import ItemGrid from '../components/ItemGrid.vue' // 我们要把列表抽离成组件，下面会写

const queryText = ref('')
const searchImage = ref(null)
const previewUrl = ref(null)
const results = ref([])
const isSearching = ref(false)
const fileInput = ref(null)

const activeTab = ref('found')
const foundItems = ref([])
const lostItems = ref([])

// 初始化加载数据
const fetchInitialData = async () => {
  // 这里我们用 search 接口 hack 一下，不传 query，只传 type 即可获取列表
  // 注意：需要后端支持 filter
  // 简单起见，我们前端获取全部再筛选，或者后端 filter_items 已支持
  try {
    const res = await axios.post('https://catnebulaaa-xmulostandfound.hf.space/api/search', new FormData) // 获取全部
    const all = res.data.results || []
    
    // 前端分类
    foundItems.value = all.filter(i => i.item_type === 'found').slice(0, 12) // 只看最新的12条
    lostItems.value = all.filter(i => i.item_type === 'lost').slice(0, 12)
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchInitialData()
})

// 处理图片搜索
const handleImageSearch = (e) => {
  const file = e.target.files[0]
  if(file) {
    searchImage.value = file
    previewUrl.value = URL.createObjectURL(file)
  }
}
const clearImage = () => {
  searchImage.value = null; previewUrl.value = null; fileInput.value.value = ''
}

// 执行搜索
const doSearch = async () => {
  if(!queryText.value && !searchImage.value) return
  isSearching.value = true
  
  const fd = new FormData()
  if(queryText.value) fd.append('query_text', queryText.value)
  if(searchImage.value) fd.append('query_image', searchImage.value)
  
  try {
    const res = await axios.post('https://catnebulaaa-xmulostandfound.hf.space', fd)
    results.value = res.data.results
  } catch(e) { console.error(e) }
}

const resetSearch = () => {
  isSearching.value = false
  queryText.value = ''
  clearImage()
  fetchInitialData()
}
</script>

<style scoped>
.home-container { background-color: #f5f7fa; min-height: 100vh; }
.hero-section {
  background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
  padding: 40px 20px 60px;
  text-align: center;
}
.main-title { color: #2c3e50; margin-bottom: 20px; text-shadow: 0 2px 4px rgba(255,255,255,0.5); }
.search-card { max-width: 700px; margin: 0 auto; border-radius: 50px; padding: 5px; }
.search-box { display: flex; gap: 10px; align-items: center; }
.img-preview-box { margin-top: 10px; display: flex; align-items: center; gap: 10px; justify-content: center;}
.img-preview-box img { height: 50px; border-radius: 4px; border: 1px solid #ddd; }

.plaza-section { max-width: 1200px; margin: -30px auto 0; position: relative; padding: 0 20px 40px; }
.section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.tabs-wrapper { background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
</style>