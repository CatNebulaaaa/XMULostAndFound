<!-- UploadView.vue -->
<template>
  <div class="upload-view">
    <el-card class="upload-card">
      <h1 class="title">📝 发布信息</h1>
      <el-form :model="form" ref="uploadFormRef" label-position="top" class="upload-form">
        
        <!-- 图片上传 -->
        <el-form-item label="物品图片 (必须)" prop="image">
          <el-upload
            ref="uploadRef"
            list-type="picture-card"
            :auto-upload="false"
            :limit="1"
            @change="handleFileChange"
            @exceed="handleFileExceed"
          >
            <el-icon><Plus /></el-icon>
            <template #file="{ file }">
              <div>
                <img class="el-upload-list__item-thumbnail" :src="file.url" alt="" />
                <span class="el-upload-list__item-actions">
                  <span class="el-upload-list__item-delete" @click="handleRemoveFile">
                    <el-icon><Delete /></el-icon>
                  </span>
                </span>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 物品描述 -->
        <el-form-item label="物品描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请尽可能详细地描述物品特征" />
        </el-form-item>
        
        <!-- 地点 -->
        <el-form-item label="地点" prop="location">
          <el-input v-model="form.location" placeholder="例如：翔安校区图书馆" />
        </el-form-item>

        <!-- 分类 -->
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择物品分类">
            <el-option label="电子产品" value="电子产品"></el-option>
            <el-option label="证件" value="证件"></el-option>
            <el-option label="钥匙" value="钥匙"></el-option>
            <el-option label="书籍" value="书籍"></el-option>
            <el-option label="其他" value="其他"></el-option>
          </el-select>
        </el-form-item>

        <!-- 联系方式 -->
        <el-form-item label="联系方式" prop="contact">
          <el-input v-model="form.contact" placeholder="V / QQ / 电话">
            <template #prepend>V / QQ</template>
          </el-input>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading" class="submit-btn">立即发布</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, genFileId } from 'element-plus';
import apiClient from '../api'; // 确认路径正确

const router = useRouter();
const loading = ref(false);
const uploadRef = ref(null);

const form = reactive({
  description: '',
  location: '',
  category: '',
  contact: '', // 后端需要这个字段
  imageFile: null
});

// 处理文件选择
const handleFileChange = (file) => {
  form.imageFile = file.raw;
};

// 处理文件移除
const handleRemoveFile = () => {
    form.imageFile = null;
    uploadRef.value.clearFiles();
};

// 处理文件超出限制
const handleFileExceed = (files) => {
  uploadRef.value.clearFiles();
  const file = files[0];
  file.uid = genFileId();
  uploadRef.value.handleStart(file);
  form.imageFile = file;
};

// 提交表单
const handleSubmit = async () => {
  if (!form.imageFile || !form.description || !form.location || !form.category || !form.contact) {
    ElMessage.error('请填写所有必填项！');
    return;
  }

  loading.value = true;
  const formData = new FormData();
  formData.append('file', form.imageFile);
  formData.append('description', form.description);
  formData.append('location', form.location);
  formData.append('category', form.category);
  // 注意：你的后端 add_item 函数并没有 contact 字段，这是一个潜在问题
  // 但为了表单完整，我们先加上
  // formData.append('contact', form.contact); 

  try {
    // 关键的 API 调用
    await apiClient.post('/api/items', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    ElMessage.success('发布成功！');
    router.push('/'); // 发布成功后跳转回首页

  } catch (error) {
    console.error('发布失败:', error);
    const errorMessage = error.response?.data?.detail || '发布失败，请检查网络或联系管理员';
    ElMessage.error(errorMessage);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.upload-view {
  display: flex;
  justify-content: center;
  padding: 20px;
}
.upload-card {
  width: 100%;
  max-width: 600px;
}
.title {
  text-align: center;
  margin-bottom: 20px;
}
.submit-btn {
  width: 100%;
}
</style>