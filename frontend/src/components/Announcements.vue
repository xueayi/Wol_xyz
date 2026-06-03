<script setup lang="ts">
defineProps<{ announcements: any[] }>()
const emit = defineEmits(['manage'])

function formatDate(dt: string) {
  return new Date(dt).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="announcements">
    <div class="section-header">
      <span class="section-title">系统公告</span>
      <span class="edit-link" @click="emit('manage')">编辑</span>
    </div>
    <div v-if="announcements.length === 0" class="empty">暂无公告</div>
    <div v-for="ann in announcements.slice(0, 3)" :key="ann.id" class="ann-item">
      <div class="ann-title">
        {{ ann.title }}
        <span v-if="ann.is_pinned" class="pin-badge">置顶</span>
      </div>
      <div class="ann-content">{{ ann.content }}</div>
      <div class="ann-time">发布于：{{ formatDate(ann.created_at) }}</div>
    </div>
  </div>
</template>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1c1c1e;
  letter-spacing: -0.3px;
}
.edit-link {
  font-size: 13px;
  color: #007AFF;
  cursor: pointer;
  font-weight: 500;
}
.ann-item {
  background: rgba(0,0,0,0.02);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 8px;
  transition: background 0.2s;
}
.ann-item:hover { background: rgba(0,0,0,0.04); }
.ann-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #1c1c1e;
}
.pin-badge {
  font-size: 10px;
  font-weight: 700;
  color: #FF9F0A;
  background: rgba(255,159,10,0.12);
  padding: 1px 6px;
  border-radius: 20px;
}
.ann-content {
  font-size: 12px;
  color: #636366;
  line-height: 1.6;
}
.ann-time {
  font-size: 11px;
  color: #aeaeb2;
  margin-top: 6px;
}
.empty {
  color: #c7c7cc;
  text-align: center;
  padding: 24px;
  font-size: 13px;
}
</style>
