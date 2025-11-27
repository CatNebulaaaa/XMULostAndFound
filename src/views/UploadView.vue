<template>
  <div class="upload-view">
    <el-card class="upload-card">
      <h1 class="title">📝 发布信息</h1>
      <el-form :model="form" ref="uploadFormRef" label-position="top" class="upload-form" @submit.prevent>

        <!-- 1. 新增：信息类型 -->
        <el-form-item label="信息类型" prop="item_type">
          <el-radio-group v-model="form.item_type">
            <el-radio-button label="found">😇 我捡到了 (失物招领)</el-radio-button>
            <el-radio-button label="lost">😭 我丢了 (寻物启事)</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 2. 图片上传 -->
        <el-form-item label="物品图片 (必须)" prop="image">
          <el-upload
            ref="uploadRef"
            list-type="picture-card"
            :auto-upload="false"
            :limit="1"
            @change="handleFileChange"
            @exceed="handleFileExceed"
            @remove="handleRemoveFile"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <!-- 3. 物品描述 -->
        <el-form-item label="物品描述 (必填)" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请尽可能详细地描述物品特征，如颜色、品牌、大小等" />
        </el-form-item>
        
        <!-- 4. 恢复并优化：地点 -->
        <el-form-item label="地点 (必填)" prop="location">
          <el-autocomplete
            v-model="form.location"
            :fetch-suggestions="queryLocations"
            placeholder="请选择或输入地点，如：德旺图书馆"
            style="width: 100%;"
            clearable
          />
        </el-form-item>

        <!-- 5. 分类 -->
        <el-form-item label="分类 (必填)" prop="category">
          <el-select v-model="form.category" placeholder="请选择物品分类" style="width: 100%;">
            <el-option label="电子产品 (手机/耳机/充电宝)" value="电子产品"></el-option>
            <el-option label="证件 (校园卡/身份证)" value="证件"></el-option>
            <el-option label="钥匙/雨伞" value="钥匙/雨伞"></el-option>
            <el-option label="书籍/文具" value="书籍/文具"></el-option>
            <el-option label="衣物/饰品" value="衣物/饰品"></el-option>
            <el-option label="其他" value="其他"></el-option>
          </el-select>
        </el-form-item>

        <!-- 6. 联系方式 -->
        <el-form-item label="联系方式 (必填)" prop="contact">
          <el-input v-model="form.contact" placeholder="微信号 / QQ号 / 手机号">
            <template #prepend>联系方式</template>
          </el-input>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading" class="submit-btn" native-type="submit">立即发布</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, genFileId } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import apiClient from '../api';

const router = useRouter();
const loading = ref(false);
const uploadRef = ref(null);

const form = reactive({
  description: '',
  location: '',
  category: '',
  contact: '',
  item_type: 'found', // 默认为 "found" (我捡到了)
  imageFile: null
});

// 预设的地点列表
const allLocations = [
  { value: '翔安校区-德旺图书馆' },
  { value: '翔安校区-主楼群（坤銮/文宣/学武/1号楼）' },
  { value: '翔安校区-一期食堂' },
  { value: '翔安校区-二期食堂' },
  { value: '翔安校区-学生公寓（芙蓉/凌云/国光）' },
  { value: '翔安校区-学生活动中心' },
  { value: '思明校区-图书馆总馆' },
  { value: '思明校区-嘉庚楼群' },
  { value: '思明校区-芙蓉餐厅' },
  { value: '思明校区-勤业餐厅' },
  { value: '思明校区-南光/芙蓉/石井宿舍区' },
  { value: '思明校区-上弦场/建南大会堂' },
  { value: '校园巴士' },
];

// 地点自动补全的查询逻辑
const queryLocations = (queryString, cb) => {
  const results = queryString
    ? allLocations.filter(item => item.value.toLowerCase().includes(queryString.toLowerCase()))
    : allLocations;
  cb(results);
};

// 文件状态处理
const handleFileChange = (file) => {
  form.imageFile = file.raw;
};

const handleRemoveFile = () => {
  form.imageFile = null;
};

const handleFileExceed = (files) => {
  uploadRef.value.clearFiles();
  const file = files[0];
  file.uid = genFileId();
  uploadRef.value.handleStart(file);
  form.imageFile = file.raw;
};

// 提交表单的核心逻辑
const handleSubmit = async () => {
  if (!form.imageFile || !form.description || !form.location || !form.category || !form.contact) {
    ElMessage.error('请将所有必填项填写完整！');
    return;
  }

  loading.value = true;
  const formData = new FormData();
  
  // 添加所有后端需要的字段，确保和后端main.py接口一致
  formData.append('file', form.imageFile);
  formData.append('description', form.description);
  formData.append('location', form.location);
  formData.append('category', form.category);
  formData.append('contact', form.contact);
  formData.append('item_type', form.item_type);

  try {
    // API请求路径为 /api/items
    await apiClient.post('/api/items', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    ElMessage.success('发布成功！即将跳转到首页...');
    setTimeout(() => router.push('/'), 1500); // 延迟跳转，给用户看提示的时间

  } catch (error) {
    console.error('发布失败:', error);
    let errorMessage = '发布失败，请稍后重试';
    if (error.response) {
      // 从后端获取更详细的错误信息
      errorMessage = error.response.data?.detail || `服务器错误 (${error.response.status})`;
    }
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
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px); /* 假设Header高度为60px */
}
.upload-card {
  width: 100%;
  max-width: 700px;
}
.title {
  text-align: center;
  margin-bottom: 25px;
  font-size: 24px;
  color: #303133;
}
.submit-btn {
  width: 100%;
  font-size: 16px;
  height: 40px;
}
/* 针对 el-form-item 的一些微调 */
.el-form-item {
  margin-bottom: 22px;
}
</style>
