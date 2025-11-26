<template>
  <el-card class="upload-card">
    <h1 class="title">📝 发布信息</h1>
    <p class="subtitle">请尽可能详细地描述物品特征</p>

    <el-form ref="formRef" :model="form" label-position="top" class="upload-form">
      
      <el-form-item label="信息类型" required>
        <el-radio-group v-model="form.type">
          <el-radio-button label="found">😇 我捡到了 (失物招领)</el-radio-button>
          <el-radio-button label="lost" disabled>😭 我丢了 (寻物启事)</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="上传图片 (AI自动识别特征)" required>
        <el-upload
          action="#"
          list-type="picture-card"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          accept="image/*"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
      </el-form-item>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="发生地点" required>
            <el-select v-model="form.location" placeholder="请选择地点" style="width: 100%;">
              <el-option label="竞丰食堂" value="竞丰食堂"></el-option>
              <el-option label="芙蓉食堂" value="芙蓉食堂"></el-option>
              <el-option label="图书馆" value="图书馆"></el-option>
              <el-option label="教学楼" value="教学楼"></el-option>
              <el-option label="其他" value="其他"></el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="物品分类" required>
            <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%;">
              <el-option label="校园卡/证件" value="校园卡/证件"></el-option>
              <el-option label="电子产品" value="电子产品"></el-option>
              <el-option label="雨伞" value="雨伞"></el-option>
              <el-option label="水杯" value="水杯"></el-option>
              <el-option label="其他" value="其他"></el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="物品描述 (颜色、品牌、特殊痕迹等)" required>
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="例如：一个黑色的小米双肩包，上面挂着一个皮卡丘挂件"
        ></el-input>
      </el-form-item>

      <el-form-item label="联系方式 (仅展示给搜索到的人)" required>
         <el-input v-model="form.contact" placeholder="请输入您的 V 或 QQ">
            <template #prepend>V / QQ</template>
         </el-input>
      </el-form-item>

      <el-form-item>
        <el-button @click="submitForm" type="primary" style="width: 100%;" :loading="loading">立即发布</el-button>
      </el-form-item>

    </el-form>
  </el-card>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import apiClient from '../api';

const router = useRouter();
const loading = ref(false);

const form = reactive({
  type: 'found',
  file: null,
  location: '',
  category: '',
  description: '',
  contact: '',
});

// 处理文件选择
const handleFileChange = (uploadFile) => {
  // el-upload 的 on-change 会在添加文件、上传成功和上传失败时都触发
  // 我们只关心文件被添加的状态
  if (uploadFile.status === 'ready') {
    form.file = uploadFile.raw;
  }
};

// 处理文件移除
const handleFileRemove = () => {
  form.file = null;
};

const submitForm = async () => {
  if (!form.file || !form.location || !form.category || !form.description || !form.contact) {
    ElMessage.error('请填写所有必填项并上传图片！');
    return;
  }
  
  loading.value = true;
  
  const formData = new FormData();
  // 注意：后端的 add_item 方法没有接收 contact 字段，这里我们先将其合并到 description 中
  const fullDescription = `${form.description} [联系方式: ${form.contact}]`;

  formData.append('file', form.file);
  formData.append('location', form.location);
  formData.append('category', form.category);
  formData.append('description', fullDescription);

  try {
    await apiClient.post('/items', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    ElMessage.success('发布成功！');
    router.push('/'); // 发布成功后跳转回主页
  } catch (error) {
    console.error('发布失败:', error);
    const errorMsg = error.response?.data?.detail || error.message || '未知错误';
    ElMessage.error(`发布失败: ${errorMsg}`);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.upload-card {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}
.title {
  text-align: center;
}
.subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
}
.upload-form {
  margin-top: 20px;
}
</style>