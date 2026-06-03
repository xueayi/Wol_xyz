<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { wakeDevice, shutdownDevice } from '../api/devices'

const props = defineProps<{ device: any }>()
const emit = defineEmits(['refresh', 'edit'])
const msg = useMessage()
const waking = ref(false)
const shutting = ref(false)

async function handleWake() {
  waking.value = true
  try {
    const { data } = await wakeDevice(props.device.id)
    if (data.success) msg.success('开机指令已发送')
    else msg.error(data.detail)
  } catch { msg.error('操作失败') }
  finally { waking.value = false; emit('refresh') }
}

async function handleShutdown() {
  shutting.value = true
  try {
    const { data } = await shutdownDevice(props.device.id)
    if (data.success) msg.success('关机指令已发送')
    else msg.error(data.detail)
  } catch (e: any) { msg.error(e.response?.data?.detail || '操作失败') }
  finally { shutting.value = false; emit('refresh') }
}

function timeAgo(dt: string | null) {
  if (!dt) return '从未'
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
  <div class="device-card" :class="{ online: device.is_online }">
    <div class="card-header">
      <div class="device-avatar" :class="{ 'avatar-online': device.is_online }">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/>
          <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
      </div>
      <div class="device-name-row">
        <span class="device-name" @click="emit('edit', device)">{{ device.name }}</span>
        <span class="status-badge" :class="device.is_online ? 'online' : 'offline'">
          {{ device.is_online ? '在线' : '离线' }}
        </span>
      </div>
    </div>

    <div class="card-body">
      <div class="info-row">
        <svg class="info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        <span class="value">{{ device.ip }}</span>
      </div>
      <div class="info-row">
        <svg class="info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2" stroke-linecap="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg>
        <span class="value mono">{{ device.mac }}</span>
      </div>
      <div class="info-row" v-if="device.adapter_name">
        <svg class="info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2" stroke-linecap="round"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
        <span class="value">{{ device.adapter_name }}</span>
      </div>
      <div class="info-row">
        <svg class="info-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <span class="value">最后在线：{{ timeAgo(device.last_seen_at) }}</span>
      </div>
    </div>

    <div class="card-actions">
      <button class="action-btn wake" :class="{ disabled: device.is_online }" :disabled="device.is_online || waking" @click="handleWake">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
        {{ waking ? '...' : '开机' }}
      </button>
      <button class="action-btn shut" :class="{ disabled: !device.shutdown_enabled }" :disabled="!device.shutdown_enabled || shutting" @click="handleShutdown">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><rect x="8" y="8" width="8" height="8" rx="1"/></svg>
        {{ shutting ? '...' : '关机' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.device-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 18px;
  border: 0.5px solid rgba(0,0,0,0.04);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.device-card.online {
  border-color: rgba(52, 199, 89, 0.25);
}
.device-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06), 0 12px 32px rgba(0,0,0,0.04);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.device-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #f2f2f7;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8e8e93;
  flex-shrink: 0;
  transition: all 0.3s;
}
.device-avatar.avatar-online {
  background: rgba(52, 199, 89, 0.12);
  color: #34C759;
}
.device-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.device-name {
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #1c1c1e;
  transition: color 0.2s;
}
.device-name:hover { color: #007AFF; }

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  white-space: nowrap;
  letter-spacing: 0.3px;
}
.status-badge.online {
  color: #34C759;
  background: rgba(52, 199, 89, 0.12);
}
.status-badge.offline {
  color: #8e8e93;
  background: rgba(142, 142, 147, 0.12);
}

.card-body { margin-bottom: 14px; }
.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 4px 0;
  color: #636366;
}
.info-icon { flex-shrink: 0; opacity: 0.5; }
.value { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.value.mono { font-family: "SF Mono", "Menlo", monospace; font-size: 12px; }

.card-actions {
  display: flex;
  gap: 8px;
}
.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px 0;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.action-btn.wake {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}
.action-btn.wake:hover:not(.disabled) {
  background: rgba(0, 122, 255, 0.18);
}
.action-btn.shut {
  background: rgba(255, 59, 48, 0.08);
  color: #FF3B30;
}
.action-btn.shut:hover:not(.disabled) {
  background: rgba(255, 59, 48, 0.15);
}
.action-btn.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
</style>
