<script setup lang="ts">
defineProps<{ logs: any[] }>()
const emit = defineEmits(['viewAll'])

const actionLabels: Record<string, string> = { wake: '开机', shutdown: '关机', scan: '扫描' }

function timeAgo(dt: string) {
  const diff = Date.now() - new Date(dt).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m}分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}小时前`
  return `${Math.floor(h / 24)}天前`
}
</script>

<template>
  <div class="recent-logs">
    <div class="section-header">
      <span class="section-title">最近触发记录</span>
      <span class="more-link" @click="emit('viewAll')">更多</span>
    </div>
    <div v-if="logs.length === 0" class="empty">暂无记录</div>
    <div v-for="log in logs" :key="log.id" class="log-row">
      <div class="log-indicator" :class="log.result" />
      <div class="log-info">
        <span class="log-device">{{ log.device_name || '未知' }}</span>
        <span class="log-action">{{ actionLabels[log.action] || log.action }}</span>
      </div>
      <span class="log-time">{{ timeAgo(log.created_at) }}</span>
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
.more-link {
  font-size: 13px;
  color: #007AFF;
  cursor: pointer;
  font-weight: 500;
}
.log-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 0.5px solid rgba(0,0,0,0.05);
}
.log-row:last-child { border-bottom: none; }
.log-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.log-indicator.success { background: #34C759; }
.log-indicator.failure { background: #FF3B30; }
.log-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.log-device {
  font-size: 13px;
  font-weight: 600;
  color: #1c1c1e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log-action {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 20px;
  background: rgba(0,0,0,0.04);
  color: #636366;
  white-space: nowrap;
}
.log-time {
  color: #aeaeb2;
  font-size: 12px;
  white-space: nowrap;
}
.empty {
  color: #c7c7cc;
  text-align: center;
  padding: 24px;
  font-size: 13px;
}
</style>
