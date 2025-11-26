<template>
  <div v-if="items.length === 0" class="empty-state">
    <el-empty :description="emptyText" />
  </div>

  <el-row v-else :gutter="20">
    <el-col
      v-for="item in items"
      :key="item.id"
      :xs="24"
      :sm="12"
      :md="8"
      :lg="6"
    >
      <el-card
        class="item-card"
        :body-style="{ padding: '0px' }"
        shadow="hover"
      >
        <div class="img-box">
          <!-- 这里的标签根据类型变色 -->
          <div class="status-tag" :class="item.item_type">
            {{ item.item_type === "found" ? "招领" : "寻物" }}
          </div>
          <el-image
            :src="`https://catnebulaaa-xmulostandfound.hf.space/api/images/${item.image_filename}`"
            fit="cover"
            class="card-img"
            loading="lazy"
          />
        </div>
        <div class="info-box">
          <div class="row-1">
            <el-tag size="small" effect="plain">{{ item.category }}</el-tag>
            <span class="location">📍 {{ item.location }}</span>
          </div>
          <p class="desc">{{ item.description }}</p>

          <div class="contact-box" v-if="item.contact">
            <el-popover placement="top" width="200" trigger="click">
              <template #reference>
                <el-button type="primary" link size="small"
                  >查看联系方式</el-button
                >
              </template>
              <div style="text-align: center">
                <p>📞 联系方式</p>
                <strong style="font-size: 16px; color: #3a7bd5">{{
                  item.contact
                }}</strong>
                <p style="font-size: 12px; color: #999; margin-top: 5px">
                  联系时请说明来自失物平台
                </p>
              </div>
            </el-popover>
          </div>
          <div class="date">{{ formatDate(item.timestamp) }}</div>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
defineProps({
  items: Array,
  emptyText: { type: String, default: "暂无数据" },
});

const formatDate = (str) => {
  if (!str) return "";
  return new Date(str).toLocaleDateString();
};
</script>

<style scoped>
.item-card {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s;
}
.item-card:hover {
  transform: translateY(-4px);
}
.img-box {
  height: 160px;
  position: relative;
  background: #eee;
}
.card-img {
  width: 100%;
  height: 100%;
}

.status-tag {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 2;
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  font-weight: bold;
}
.status-tag.found {
  background: #67c23a;
} /* 绿色 */
.status-tag.lost {
  background: #f56c6c;
} /* 红色 */

.info-box {
  padding: 12px;
}
.row-1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.location {
  font-size: 12px;
  color: #666;
}
.desc {
  font-size: 14px;
  color: #333;
  height: 40px;
  overflow: hidden;
  margin: 0 0 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.contact-box {
  border-top: 1px dashed #eee;
  padding-top: 8px;
  margin-bottom: 5px;
}
.date {
  font-size: 12px;
  color: #aaa;
  text-align: right;
}
</style>
