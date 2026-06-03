<script setup lang="ts">
defineProps<{ channels: any[] }>()
const emit = defineEmits(['add'])
</script>

<template>
  <div class="channel-status">
    <div class="section-header">
      <span class="section-title">通知渠道状态</span>
      <span class="manage-link" @click="emit('add')">+ 新建</span>
    </div>
    <div v-if="channels.length === 0" class="empty">暂未配置通知渠道</div>
    <div v-for="ch in channels" :key="ch.id" class="channel-row">
      <div class="ch-icon" :class="ch.type">
        <svg v-if="ch.type === 'email'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
      </div>
      <span class="ch-name">{{ ch.name }}</span>
      <span class="ch-status" :class="ch.enabled ? 'on' : 'off'">
        {{ ch.enabled ? '启用' : '禁用' }}
      </span>
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
.manage-link {
  font-size: 13px;
  color: #007AFF;
  cursor: pointer;
  font-weight: 500;
}
.channel-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 0.5px solid rgba(0,0,0,0.06);
}
.channel-row:last-child { border-bottom: none; }
.ch-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ch-icon.email {
  background: rgba(0,122,255,0.1);
  color: #007AFF;
}
.ch-icon.webhook {
  background: rgba(88,86,214,0.1);
  color: #5856D6;
}
.ch-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #1c1c1e;
}
.ch-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}
.ch-status.on {
  color: #34C759;
  background: rgba(52,199,89,0.12);
}
.ch-status.off {
  color: #8e8e93;
  background: rgba(142,142,147,0.12);
}
.empty {
  color: #c7c7cc;
  text-align: center;
  padding: 24px;
  font-size: 13px;
}
</style>
