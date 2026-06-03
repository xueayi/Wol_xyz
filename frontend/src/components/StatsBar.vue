<script setup lang="ts">
defineProps<{
  stats: {
    total_devices: number
    online_devices: number
    group_count: number
    schedule_count: number
    today_triggers: number
  }
}>()

const items = [
  { key: 'total_devices', label: '总设备数', color: '#007AFF', bg: 'rgba(0,122,255,0.1)' },
  { key: 'online_devices', label: '在线设备', color: '#34C759', bg: 'rgba(52,199,89,0.1)' },
  { key: 'group_count', label: '设备分组', color: '#FF9F0A', bg: 'rgba(255,159,10,0.1)' },
  { key: 'schedule_count', label: '定时任务', color: '#5856D6', bg: 'rgba(88,86,214,0.1)' },
  { key: 'today_triggers', label: '今日触发', color: '#FF3B30', bg: 'rgba(255,59,48,0.1)' },
]
</script>

<template>
  <div class="stats-bar">
    <div v-for="item in items" :key="item.key" class="stat-card">
      <div class="stat-dot" :style="{ background: item.color }" />
      <div class="stat-info">
        <div class="stat-value" :style="{ color: item.color }">
          <template v-if="item.key === 'online_devices'">
            {{ stats.online_devices }}/{{ stats.total_devices }}
          </template>
          <template v-else>
            {{ (stats as any)[item.key] }}
          </template>
        </div>
        <div class="stat-label">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-bar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 18px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 0.5px solid rgba(0,0,0,0.04);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
  transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94), box-shadow 0.2s;
}
.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.04);
}
.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1.1;
}
.stat-label {
  font-size: 12px;
  color: #8e8e93;
  margin-top: 3px;
  font-weight: 500;
}
@media (max-width: 1024px) {
  .stats-bar { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
  .stats-bar { grid-template-columns: repeat(2, 1fr); }
}
</style>
