<template>
  <div style="max-width: 600px; margin: 40px auto; padding: 0 20px;">
    <h2 style="text-align: center; margin-bottom: 30px; color: #333;">发布失物信息</h2>

    <!-- 外层el-form：确保有正确的闭合和属性 -->
    <el-form
        ref="uploadFormRef"
        :model="form"
        :rules="formRules"
        style="padding: 30px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);"
    >
      <!-- 1. 图片上传（ElUpload组件） -->
      <el-form-item label="物品图片（必填）" style="margin-bottom: 25px;">
        <el-upload
            class="image-upload"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            :file-list="fileList"
            accept="image/jpeg,image/png"
            list-type="picture-card"
        >
          <i class="el-icon-plus"></i> <!-- 正确的图标标签 -->
          <template #file="{ file }">
            <div>
              <img :src="file.url" class="el-upload-list__item-thumbnail" alt="预览图">
              <span class="el-upload-list__item-actions">
                <span @click="handleRemove(file)">
                  <i class="el-icon-delete"></i> <!-- 正确的图标标签 -->
                </span>
              </span>
            </div>
          </template>
        </el-upload>
        <p style="margin-top: 5px; font-size: 12px; color: #666;">
          支持JPG、PNG格式，单张图片不超过5MB
        </p>
      </el-form-item>

      <!-- 2. 丢失地点（ElSelect + ElOption） -->
      <el-form-item label="丢失地点" prop="location" style="margin-bottom: 25px;">
        <el-select
            v-model="form.location"
            placeholder="请选择丢失地点"
            style="width: 100%;"
        >
          <el-option value="" label="请选择丢失地点"></el-option>
          <el-option value="教学楼" label="教学楼"></el-option>
          <el-option value="食堂" label="食堂"></el-option>
          <el-option value="餐厅" label="餐厅"></el-option>
          <el-option value="图书馆" label="图书馆"></el-option>
          <el-option value="操场" label="操场"></el-option>
          <el-option value="宿舍区" label="宿舍区"></el-option>
        </el-select>
      </el-form-item>

      <!-- 3. 物品分类（ElSelect + ElOption） -->
      <el-form-item label="物品分类" prop="category" style="margin-bottom: 25px;">
        <el-select
            v-model="form.category"
            placeholder="请选择物品分类"
            style="width: 100%;"
        >
          <el-option value="" label="请选择物品分类"></el-option>
          <el-option value="电子设备" label="电子设备（手机、电脑等）"></el-option>
          <el-option value="证件卡片" label="证件卡片（身份证、校园卡等）"></el-option>
          <el-option value="箱包配饰" label="箱包配饰（背包、钱包等）"></el-option>
          <el-option value="学习用品" label="学习用品（书本、文具等）"></el-option>
          <el-option value="衣物鞋帽" label="衣物鞋帽（衣服、鞋子等）"></el-option>
          <el-option value="其他物品" label="其他物品"></el-option>
        </el-select>
      </el-form-item>

      <!-- 4. 物品描述（ElInput文本域） -->
      <el-form-item label="物品描述" prop="description" style="margin-bottom: 25px;">
        <el-input
            type="textarea"
            v-model="form.description"
            rows="4"
            placeholder="请详细描述物品特征"
            style="resize: none;"
        ></el-input>
      </el-form-item>

      <!-- 5. 联系电话（ElInput） -->
      <el-form-item label="联系电话" style="margin-bottom: 25px;">
        <el-input
            v-model="form.phone"
            placeholder="请输入联系电话（选填）"
            type="tel"
        ></el-input>
      </el-form-item>

      <!-- 6. 提交按钮 -->
      <el-form-item>
        <el-button
            type="primary"
            @click="handleSubmit"
            :disabled="isSubmitting"
            style="width: 100%;"
        >
          <span v-if="!isSubmitting">提交失物信息</span>
          <span v-if="isSubmitting">提交中...</span>
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage, ElLoading } from 'element-plus';
import axios from 'axios';

// 表单数据
const form = ref({
  location: '',
  category: '',
  description: '',
  phone: ''
});

// 校验规则
const formRules = ref({
  location: [{ required: true, message: '请选择丢失地点', trigger: 'change' }],
  category: [{ required: true, message: '请选择物品分类', trigger: 'change' }],
  description: [{ required: true, message: '请填写物品描述', trigger: 'blur' }]
});

// 图片相关
const fileList = ref([]);
const selectedFile = ref(null);
const uploadFormRef = ref(null);
const isSubmitting = ref(false);

// 图片上传前校验
// <script setup> 里的代码：替换旧函数+补全依赖变量


// 2. 粘贴新的beforeUpload函数（替换旧函数）
const beforeUpload = (file) => {
  const isImage = ['image/jpeg', 'image/png'].includes(file.type);
  if (!isImage) {
    ElMessage.error('仅支持JPG、PNG格式！');
    return false; // 校验失败，拦截文件（符合项目文档“手动提交”需求）
  }
  const isLt5MB = file.size <= 5 * 1024 * 1024; // 5MB限制（项目文档要求）
  if (!isLt5MB) {
    ElMessage.error('图片不能超过5MB！');
    return false;
  }
  return true; // 校验通过，允许后续处理
};

// 3. 粘贴新的handleFileChange函数（替换旧函数）
const handleFileChange = (file) => {
  const rawFile = file.raw; // ElUpload的文件需取.raw（原生文件对象）
  if (!rawFile) return;

  // 生成预览图（用FileReader，符合项目“预览需求”）
  const reader = new FileReader();
  reader.onload = (e) => {
    file.url = e.target.result; // 给文件加预览地址，模板能显示图片
  };
  reader.readAsDataURL(rawFile);

  // 保存文件（后续提交给后端用，符合POST /api/items接口的file参数要求）
  selectedFile.value = rawFile;
  fileList.value = [file]; // 更新文件列表，模板能显示选中的图片
};

// 4. 粘贴新的handleRemove函数（替换旧函数）
const handleRemove = (file) => {
  // 从列表中删除当前文件（用uid唯一标识，避免删错）
  fileList.value = fileList.value.filter(item => item.uid !== file.uid);
  selectedFile.value = null; // 清空提交用的文件，避免提交删除的图片
};



// 提交表单
const handleSubmit = async () => {
  // 表单校验
  const valid = await new Promise(resolve => {
    uploadFormRef.value.validate(valid => resolve(valid));
  });
  if (!valid) return;

  // 检查图片
  if (!selectedFile.value) {
    ElMessage.warning('请上传物品图片');
    return;
  }

  // 提交逻辑
  const loading = ElLoading.service({ text: '提交中...' });
  isSubmitting.value = true;
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('location', form.value.location);
    formData.append('category', form.value.category);
    formData.append('description', form.value.description);
    if (form.value.phone) formData.append('phone', form.value.phone);

    const res = await axios.post('/api/items', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    ElMessage.success(`提交成功！ID：${res.data.id}`);
    uploadFormRef.value.resetFields();
    fileList.value = [];
    selectedFile.value = null;
  } catch (err) {
    ElMessage.error('提交失败，请重试');
  } finally {
    loading.close();
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
/* 修复图标和上传框样式 */
::v-deep .el-upload--picture-card {
  width: 100%;
  height: 120px;
  line-height: 120px;
}

/* 1. 确保整个上传卡片容器可点击（宽高足够，无遮挡） */
::v-deep .el-upload--picture-card {
  width: 200px !important; /* 固定宽度，足够大 */
  height: 200px !important; /* 固定高度，足够大 */
  line-height: 200px !important; /* 图标垂直居中 */
  position: relative !important; /* 确保内部按钮能相对它定位 */
  border: 2px dashed #ccc !important; /* 明显的边框，方便看到点击范围 */
  background: #f9f9f9 !important; /* 浅色背景，区分区域 */
}

/* 2. 关键：让内部的点击按钮充满整个卡片（之前只有图标大小） */
::v-deep .el-upload--picture-card .el-upload {
  position: absolute !important; /* 脱离文档流，覆盖整个卡片 */
  top: 0 !important;
  left: 0 !important;
  width: 100% !important; /* 宽度充满卡片 */
  height: 100% !important; /* 高度充满卡片 */
  display: flex !important;
  align-items: center !important; /* 图标水平居中 */
  justify-content: center !important; /* 图标垂直居中 */
}

/* 3. 优化图标显示（避免图标过小导致误判） */
::v-deep .el-icon-plus {
  font-size: 40px !important; /* 放大图标，更明显 */
  color: #999 !important;
}

</style>