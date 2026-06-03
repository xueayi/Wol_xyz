<script setup lang="ts">
const emit = defineEmits(['action'])

const actions = [
  { key: 'scan', label: '扫描局域网', icon: 'scan', color: '#007AFF' },
  { key: 'addDevice', label: '手动添加', icon: 'plus', color: '#34C759' },
  { key: 'schedules', label: '定时任务', icon: 'clock', color: '#FF9F0A' },
  { key: 'triggers', label: '触发源', icon: 'zap', color: '#FF6B35' },
  { key: 'wolConfig', label: 'WoL 配置', icon: 'gear', color: '#5856D6' },
  { key: 'guide', label: '使用指引', icon: 'book', color: '#007AFF' },
]
</script>

<template>
  <div class="quick-actions">
    <div class="section-title">功能设置</div>
    <div class="actions-grid">
      <div v-for="a in actions" :key="a.key" class="action-btn" @click="emit('action', a.key)">
        <div class="action-icon" :style="{ background: a.color + '14', color: a.color }">
          <svg v-if="a.icon==='scan'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <svg v-if="a.icon==='plus'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          <svg v-if="a.icon==='clock'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <svg v-if="a.icon==='zap'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <svg v-if="a.icon==='gear'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <svg v-if="a.icon==='book'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
        </div>
        <span class="action-label">{{ a.label }}</span>
      </div>
    </div>
    <div class="project-link" @click="emit('action', 'about')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
      <span>项目说明</span>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 14px;
  color: #1c1c1e;
  letter-spacing: -0.3px;
}
.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}
.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 4px 10px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
}
.action-btn:hover { background: rgba(0,0,0,0.03); }
.action-btn:active { transform: scale(0.96); }
.action-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}
.action-btn:hover .action-icon { transform: scale(1.05); }
.action-label {
  font-size: 11px;
  color: #636366;
  font-weight: 500;
}
.project-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  cursor: pointer;
  color: #007AFF;
  font-size: 13px;
  font-weight: 500;
  border-radius: 10px;
  transition: background 0.2s;
}
.project-link:hover { background: rgba(0,122,255,0.06); }
</style>
