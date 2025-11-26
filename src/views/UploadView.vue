<template>
  <div class="upload-container">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>📝 发布信息</h2>
          <p>请尽可能详细地描述物品特征</p>
        </div>
      </template>

      <el-form :model="form" label-position="top" size="large">
        
        <!-- 1. 类型选择 (核心新功能) -->
        <el-form-item label="信息类型">
          <el-radio-group v-model="form.item_type" fill="#3a7bd5">
            <el-radio-button label="found">😇 我捡到了 (失物招领)</el-radio-button>
            <el-radio-button label="lost">😭 我丢了 (寻物启事)</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 2. 图片上传 -->
        <el-form-item label="上传图片 (AI自动识别特征)">
          <el-upload
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleRemove"
            list-type="picture-card"
            class="upload-area"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <!-- 3. 地点选择 (已更新 XMU 专属地点) -->
            <el-form-item label="发生地点">
              <el-select v-model="form.location" placeholder="请选择地点" style="width: 100%">
                <el-option v-for="loc in locations" :key="loc" :label="loc" :value="loc" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <!-- 4. 物品分类 (已更新) -->
            <el-form-item label="物品分类">
              <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="物品描述 (颜色、品牌、特殊痕迹等)">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="例如：在三家村路口捡到的，黑色水杯，上面有哆啦A梦贴纸" />
        </el-form-item>

        <el-form-item label="联系方式 (仅展示给搜索到的人)">
          <el-input v-model="form.contact" placeholder="微信号 / 手机号 (例如: V: xmu123456)" >
            <template #prefix><el-icon><Message /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" class="submit-btn" @click="submitUpload" :loading="loading" round>
            立即发布
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Plus, Message } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const file = ref(null)

const form = ref({
  item_type: 'found', // 默认是捡到了
  description: '',
  location: '',
  category: '',
  contact: ''
})

// 更新后的地点列表
const locations = [
  '思源食堂', '竞丰食堂', '丰庭食堂', '国光', '映雪', 
  '凌云', '学武楼', '文宣楼', '坤銮楼', '一号楼', 
  '图书馆', '一期操场', '二期操场', '其他区域'
]

// 更新后的分类列表
const categories = [
  '校园卡/证件', '电子产品', '书籍/教材', '雨伞/遮阳伞', 
  '水杯/日用品', '衣物/鞋帽', '运动器材', '钥匙/门禁卡', '其他'
]

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
}
const handleRemove = () => {
  file.value = null
}

const submitUpload = async () => {
  if (!file.value) return ElMessage.warning("为了提高匹配率，请务必上传一张图片")
  if (!form.value.description) return ElMessage.warning("请填写描述")
  
  loading.value = true
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('description', form.value.description)
  formData.append('location', form.value.location)
  formData.append('category', form.value.category)
  formData.append('item_type', form.value.item_type)
  formData.append('contact', form.value.contact)

  try {
    await axios.post('https://catnebulaaa-xmulostandfound.hf.space', formData)
    ElMessage.success('发布成功！')
    // 发布成功后跳转回首页
    setTimeout(() => router.push('/'), 1000)
  } catch (e) {
    ElMessage.error('发布失败：' + e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload-container {
  max-width: 800px;
  margin: 20px auto;
}
.upload-card {
  border-radius: 12px;
}
.card-header h2 { margin: 0; color: #333; }
.card-header p { margin: 5px 0 0; color: #999; font-size: 14px; }
.submit-btn { width: 100%; font-weight: bold; font-size: 16px; padding: 22px 0; }
</style>