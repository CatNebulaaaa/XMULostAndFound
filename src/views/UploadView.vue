<!-- frontend/src/views/UploadView.vue -->
<template>
  <div class="upload-container">
    <div class="form-card">
      <div class="card-header">
        <h2>📝 发布信息</h2>
        <p class="subtitle">请尽可能详细地描述物品特征</p>
      </div>

      <el-form :model="form" ref="uploadFormRef" label-position="top">
        
        <!-- 1. 信息类型切换 (还原了大按钮样式) -->
        <el-form-item label="信息类型">
          <div class="type-selector">
            <div 
              class="type-btn" 
              :class="{ active: form.item_type === 'found' }"
              @click="form.item_type = 'found'"
            >
              😇 我捡到了 (失物招领)
            </div>
            <div 
              class="type-btn" 
              :class="{ active: form.item_type === 'lost' }"
              @click="form.item_type = 'lost'"
            >
              😭 我丢了 (寻物启事)
            </div>
          </div>
        </el-form-item>

        <!-- 2. 图片上传 (还原了 Picture Card 样式) -->
        <el-form-item label="上传图片 (AI自动识别特征)">
          <el-upload
            ref="uploadRef"
            list-type="picture-card"
            :auto-upload="false"
            :limit="1"
            @change="handleFileChange"
            @remove="handleRemoveFile"
            @exceed="handleFileExceed"
            class="custom-upload"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <!-- 3. 地点和分类 (还原了并排布局) -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发生地点">
              <el-autocomplete
                v-model="form.location"
                :fetch-suggestions="queryLocations"
                placeholder="思源食堂"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="物品分类">
              <el-select v-model="form.category" placeholder="校园卡/证件" style="width: 100%;">
                <el-option label="电子产品" value="电子产品" />
                <el-option label="证件" value="证件" />
                <el-option label="书籍" value="书籍" />
                <el-option label="钥匙/雨伞" value="钥匙/雨伞" />
                <el-option label="衣物" value="衣物" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 4. 描述 -->
        <el-form-item label="物品描述 (颜色、品牌、特殊痕迹等)">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3" 
            placeholder="学生卡" 
          />
        </el-form-item>

        <!-- 5. 联系方式 -->
        <el-form-item label="联系方式 (仅展示给搜索到的人)">
          <el-input v-model="form.contact" placeholder="12123">
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 提交按钮 -->
        <div class="submit-area">
          <el-button type="primary" size="large" class="submit-btn" @click="handleSubmit" :loading="loading">
            立即发布
          </el-button>
        </div>

      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, genFileId } from 'element-plus';
import { Plus, Message } from '@element-plus/icons-vue';
import apiClient from '../api';

const router = useRouter();
const loading = ref(false);
const uploadRef = ref(null);

const form = reactive({
  item_type: 'found', // 默认为 "found"
  location: '',
  category: '',
  description: '',
  contact: '',
  imageFile: null
});

// 地点预设
const allLocations = [
  { value: '思源食堂' }, { value: '德旺图书馆' }, { value: '芙蓉餐厅' },
  { value: '勤业餐厅' }, { value: '嘉庚楼' }, { value: '主楼群' },
  { value: '上弦场' }, { value: '南光/芙蓉宿舍' }
];
const queryLocations = (qs, cb) => {
  const results = qs ? allLocations.filter(i => i.value.toLowerCase().includes(qs.toLowerCase())) : allLocations;
  cb(results);
};

// 文件处理
const handleFileChange = (file) => { form.imageFile = file.raw; };
const handleRemoveFile = () => { form.imageFile = null; };
const handleFileExceed = (files) => {
  uploadRef.value.clearFiles();
  const file = files[0];
  file.uid = genFileId();
  uploadRef.value.handleStart(file);
  form.imageFile = file.raw;
};

// 提交逻辑 (保留了修复后的核心逻辑)
const handleSubmit = async () => {
  if (!form.imageFile || !form.description || !form.location || !form.category || !form.contact) {
    ElMessage.error('请填写完整信息（图片、描述、地点、分类、联系方式）');
    return;
  }

  loading.value = true;
  const formData = new FormData();
  formData.append('file', form.imageFile);
  formData.append('description', form.description);
  formData.append('location', form.location);
  formData.append('category', form.category);
  formData.append('contact', form.contact);     // 必传
  formData.append('item_type', form.item_type); // 必传

  try {
    await apiClient.post('/api/items', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    ElMessage.success('发布成功！');
    setTimeout(() => router.push('/'), 1000);
  } catch (error) {
    console.error(error);
    ElMessage.error(error.response?.data?.detail || '发布失败');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.upload-container {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
  background-color: #f9f9f9;
  min-height: 100vh;
}

.form-card {
  width: 100%;
  max-width: 800px;
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.card-header {
  margin-bottom: 30px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.card-header h2 {
  font-size: 24px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.subtitle {
  color: #999;
  margin-top: 5px;
  font-size: 14px;
}

/* 还原大按钮样式 */
.type-selector {
  display: flex;
  gap: 20px;
}

.type-btn {
  flex: 1;
  padding: 12px;
  text-align: center;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: bold;
  color: #606266;
}

.type-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.type-btn.active {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
}

.submit-btn {
  width: 100%;
  margin-top: 20px;
  border-radius: 20px;
  font-size: 16px;
}
</style>