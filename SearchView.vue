<template>
  <div class="search-view">
    <!-- 搜索容器 -->
    <div class="search-container">
      <h2 class="search-title">
        <i class="el-icon-search"></i>多模态物品搜索
      </h2>
      
      <!-- 筛选器区域 -->
      <el-form :inline="true" class="filter-row">
        <el-form-item label="物品分类">
          <el-select v-model="filters.category" placeholder="请选择分类" clearable>
            <el-option label="电子产品" value="electronics"></el-option>
            <el-option label="服装配饰" value="clothing"></el-option>
            <el-option label="家居用品" value="home"></el-option>
            <el-option label="书籍文档" value="books"></el-option>
            <el-option label="其他" value="others"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="地点">
          <el-select v-model="filters.location" placeholder="请选择地点" clearable>
            <el-option label="办公室" value="office"></el-option>
            <el-option label="家" value="home"></el-option>
            <el-option label="公共场所" value="public"></el-option>
            <el-option label="其他" value="others"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable>
          </el-date-picker>
        </el-form-item>
      </el-form>
      
      <!-- 多模态输入区域 -->
      <div class="input-row">
        <div class="search-input">
          <el-input
            v-model="searchText"
            placeholder="请输入物品描述或关键词"
            clearable
            @keyup.enter="performSearch">
            <template #prefix>
              <i class="el-icon-search"></i>
            </template>
          </el-input>
        </div>
        
        <div style="width: 200px;">
          <el-upload
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageUpload">
            <div class="upload-area">
              <i class="el-icon-picture-outline upload-icon"></i>
              <div class="upload-text">上传图片搜索</div>
            </div>
          </el-upload>
        </div>
      </div>
      
      <div class="search-button">
        <el-button type="primary" @click="performSearch" :loading="searching">
          <i class="el-icon-search"></i> 搜索
        </el-button>
      </div>
    </div>
    
    <!-- 结果展示区域 -->
    <div class="results-container">
      <h2 class="results-title">
        <i class="el-icon-tickets"></i>搜索结果
      </h2>
      
      <div v-if="searchResults.length > 0" class="results-grid">
        <div v-for="(item, index) in searchResults" :key="index" class="result-card">
          <el-image
            class="result-image"
            :src="item.image"
            :preview-src-list="[item.image]"
            fit="cover"
            :loading="item.loading"
            :z-index="9999">
            <template #error>
              <div class="image-slot">
                <i class="el-icon-picture-outline"></i>
              </div>
            </template>
          </el-image>
          
          <div class="result-info">
            <div class="result-title">{{ item.title }}</div>
            
            <div class="result-meta">
              <span>{{ item.location }}</span>
              <span class="similarity-score">{{ item.similarity }}% 匹配</span>
            </div>
            
            <div class="result-meta">
              <span>{{ item.date }}</span>
              <span>{{ item.category }}</span>
            </div>
            
            <div class="tags-container">
              <span v-for="(tag, tagIndex) in item.tags" :key="tagIndex" class="tag">
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="no-results">
        <i class="el-icon-search no-results-icon"></i>
        <p>暂无搜索结果，请尝试其他搜索条件</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'

export default {
  name: 'SearchView',
  data() {
    return {
      // 筛选条件
      filters: {
        category: '',
        location: '',
        dateRange: []
      },
      // 搜索文本
      searchText: '',
      // 搜索结果
      searchResults: [],
      // 搜索状态
      searching: false,
      // 模拟搜索结果数据
      mockResults: [
        {
          id: 1,
          title: '黑色无线耳机',
          image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
          location: '办公室',
          date: '2023-10-15',
          category: '电子产品',
          similarity: 92,
          tags: ['无线', '蓝牙', '音乐', '便携']
        },
        {
          id: 2,
          title: '棕色皮质钱包',
          image: 'https://images.unsplash.com/photo-1556742044-3c6cbf8c0e8c?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
          location: '家',
          date: '2023-10-10',
          category: '配饰',
          similarity: 87,
          tags: ['皮革', '棕色', '卡片', '现金']
        },
        {
          id: 3,
          title: 'MacBook Pro',
          image: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
          location: '办公室',
          date: '2023-10-05',
          category: '电子产品',
          similarity: 95,
          tags: ['苹果', '笔记本', '工作', '编程']
        },
        {
          id: 4,
          title: '蓝色水杯',
          image: 'https://images.unsplash.com/photo-1544145945-f90425340c7e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60',
          location: '公共场所',
          date: '2023-10-01',
          category: '家居用品',
          similarity: 78,
          tags: ['蓝色', '塑料', '饮水', '便携']
        }
      ]
    }
  },
  mounted() {
    // 初始化时显示一些结果
    this.searchResults = this.mockResults
  },
  methods: {
    // 执行搜索
    performSearch() {
      if (!this.searchText && !this.filters.category && !this.filters.location && this.filters.dateRange.length === 0) {
        ElMessage.warning('请输入搜索条件')
        return
      }
      
      this.searching = true
      
      // 模拟搜索延迟
      setTimeout(() => {
        // 在实际应用中，这里会调用后端API
        // 现在使用模拟数据
        this.searchResults = this.mockResults
        this.searching = false
        
        ElMessage.success(`找到 ${this.mockResults.length} 个结果`)
      }, 1000)
    },
    
    // 处理图片上传
    handleImageUpload(file) {
      ElMessage.info(`已选择图片: ${file.name}`)
      // 在实际应用中，这里会处理图片并发送到后端进行搜索
      // 现在模拟搜索
      this.performSearch()
    }
  }
}
</script>

<style scoped>
.search-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.search-title {
  font-size: 18px;
  margin-bottom: 15px;
  color: #303133;
  display: flex;
  align-items: center;
}

.search-title i {
  margin-right: 8px;
  color: #409eff;
}

.filter-row {
  margin-bottom: 15px;
}

.input-row {
  display: flex;
  gap: 15px;
  align-items: flex-end;
}

.search-input {
  flex: 1;
}

.upload-area {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  padding: 10px;
  text-align: center;
  background-color: #fafafa;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #409eff;
}

.upload-icon {
  font-size: 40px;
  color: #c0c4cc;
  margin-bottom: 10px;
}

.upload-text {
  color: #606266;
  font-size: 14px;
}

.results-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.results-title {
  font-size: 18px;
  margin-bottom: 15px;
  color: #303133;
  display: flex;
  align-items: center;
}

.results-title i {
  margin-right: 8px;
  color: #67c23a;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.result-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
}

.result-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.result-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.result-info {
  padding: 15px;
}

.result-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.result-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
  color: #909399;
}

.similarity-score {
  color: #67c23a;
  font-weight: bold;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 10px;
}

.tag {
  background-color: #ecf5ff;
  color: #409eff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.no-results {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.no-results-icon {
  font-size: 48px;
  margin-bottom: 15px;
  color: #c0c4cc;
}

.search-button {
  margin-top: 15px;
}