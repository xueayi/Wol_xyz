<script setup lang="ts">
defineProps<{
  triggers: any[]
  status: Record<string, string>
}>()
const emit = defineEmits(['manage'])

const typeLabel: Record<string, string> = {
  http_api: 'API',
  bemfa: '巴法云',
  mqtt: 'MQTT',
  telegram: 'Telegram',
}

function connectionState(trigger: any, status: Record<string, string>): string {
  if (!trigger.enabled) return 'disabled'
  return status[trigger.id] || 'disconnected'
}

function stateLabel(state: string): string {
  switch (state) {
    case 'connected': return '在线'
    case 'connecting': return '连接中'
    case 'disconnected': return '离线'
    case 'disabled': return '禁用'
    default: return '未知'
  }
}
</script>

<template>
  <div class="trigger-status">
    <div class="section-header">
      <span class="section-title">触发源状态</span>
      <span class="manage-link" @click="emit('manage')">管理</span>
    </div>
    <div v-if="triggers.length === 0" class="empty">暂未配置触发源</div>
    <div v-for="t in triggers" :key="t.id" class="trigger-row">
      <div class="t-icon" :class="t.type">
        <svg v-if="t.type === 'http_api'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/></svg>
        <svg v-else-if="t.type === 'bemfa'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>
        <svg v-else-if="t.type === 'mqtt'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        <svg v-else-if="t.type === 'telegram'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 5L2 12.5l7 1M21 5l-4 15-7.5-7.5M21 5l-12 8"/></svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
      </div>
      <div class="t-info">
        <span class="t-name">{{ t.name }}</span>
        <span class="t-type">{{ typeLabel[t.type] || t.type }}</span>
      </div>
      <div class="t-state" :class="connectionState(t, status)">
        <span class="state-dot" />
        <span class="state-text">{{ stateLabel(connectionState(t, status)) }}</span>
      </div>
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
.trigger-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 0.5px solid rgba(0,0,0,0.06);
}
.trigger-row:last-child { border-bottom: none; }
.t-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.t-icon.http_api {
  background: rgba(52,199,89,0.1);
  color: #34C759;
}
.t-icon.bemfa {
  background: rgba(255,159,10,0.1);
  color: #FF9F0A;
}
.t-icon.mqtt {
  background: rgba(88,86,214,0.1);
  color: #5856D6;
}
.t-icon.telegram {
  background: rgba(0,136,204,0.1);
  color: #0088CC;
}
.t-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.t-name {
  font-size: 14px;
  font-weight: 500;
  color: #1c1c1e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.t-type {
  font-size: 11px;
  color: #8e8e93;
}
.t-state {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}
.state-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.state-text {
  font-size: 11px;
  font-weight: 600;
}
.t-state.connected .state-dot { background: #34C759; }
.t-state.connected .state-text { color: #34C759; }
.t-state.connecting .state-dot { background: #FF9F0A; animation: pulse 1.5s ease-in-out infinite; }
.t-state.connecting .state-text { color: #FF9F0A; }
.t-state.disconnected .state-dot { background: #FF3B30; }
.t-state.disconnected .state-text { color: #FF3B30; }
.t-state.disabled .state-dot { background: #c7c7cc; }
.t-state.disabled .state-text { color: #8e8e93; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.empty {
  color: #c7c7cc;
  text-align: center;
  padding: 24px;
  font-size: 13px;
}
</style>
