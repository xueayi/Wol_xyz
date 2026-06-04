<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { wakeDevice, shutdownDevice } from '../api/devices'

const props = defineProps<{ device: any; viewMode?: 'card' | 'list'; batchMode?: boolean; selected?: boolean }>()
const emit = defineEmits(['refresh', 'edit', 'toggle-select'])
const msg = useMessage()
const waking = ref(false)
const shutting = ref(false)

const deviceIcon = computed(() => {
  const icons: Record<string, string> = {
    windows: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 12h18M12 3v18"/>',
    macos: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
    linux: '<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="14" y2="10"/><path d="M8 14h4"/>',
    iphone: '<rect x="5" y="1" width="14" height="22" rx="3"/><line x1="11" y1="18" x2="13" y2="18"/>',
    ipad: '<rect x="3" y="2" width="18" height="20" rx="2"/><line x1="11" y1="18" x2="13" y2="18"/>',
    android: '<rect x="5" y="8" width="14" height="13" rx="2"/><line x1="9" y1="4" x2="9" y2="7"/><line x1="15" y1="4" x2="15" y2="7"/><path d="M7 4a5 5 0 0 1 10 0"/>',
    watch: '<circle cx="12" cy="12" r="7"/><line x1="12" y1="5" x2="12" y2="1"/><line x1="12" y1="23" x2="12" y2="19"/><polyline points="12 9 12 12 14 14"/>',
    nas: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><circle cx="7" cy="6" r="1"/><circle cx="7" cy="12" r="1"/><circle cx="7" cy="18" r="1"/>',
    router: '<rect x="2" y="10" width="20" height="8" rx="2"/><circle cx="7" cy="14" r="1"/><circle cx="11" cy="14" r="1"/><line x1="16" y1="10" x2="18" y2="4"/><line x1="12" y1="10" x2="12" y2="6"/>',
    iot: '<circle cx="12" cy="12" r="4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>',
    computer: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
    other: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  }
  return icons[props.device.device_type] || icons.computer
})

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
  const timestamp = dt.endsWith('Z') || dt.includes('+') ? dt : dt + 'Z'
  const diff = Date.now() - new Date(timestamp).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m}分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}小时前`
  return `${Math.floor(h / 24)}天前`
}
</script>

<template>
  <!-- Card mode -->
  <div v-if="viewMode !== 'list'" class="device-card" :class="{ online: device.is_online, 'batch-selected': batchMode && selected }">
    <div class="card-header">
      <div v-if="batchMode" class="batch-checkbox" @click.stop="emit('toggle-select', device.id)">
        <div class="checkbox-inner" :class="{ checked: selected }">
          <svg v-if="selected" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
      </div>
      <div v-if="!batchMode" class="device-avatar" :class="{ 'avatar-online': device.is_online }">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" v-html="deviceIcon"></svg>
      </div>
      <div class="device-name-row">
        <span class="device-name" @click="emit('edit', device)">{{ device.name }}</span>
        <span class="status-badge" :class="device.is_online ? 'online' : 'offline'">
          {{ device.is_online ? '在线' : '离线' }}
        </span>
      </div>
      <button v-if="!batchMode" class="edit-btn" @click.stop="emit('edit', device)" title="编辑设备">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
      </button>
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

  <!-- List mode -->
  <div v-else class="device-list-row" :class="{ online: device.is_online, 'batch-selected': batchMode && selected }">
    <div v-if="batchMode" class="batch-checkbox" @click.stop="emit('toggle-select', device.id)">
      <div class="checkbox-inner" :class="{ checked: selected }">
        <svg v-if="selected" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      </div>
    </div>
    <div class="list-status-dot" :class="device.is_online ? 'dot-online' : 'dot-offline'" />
    <div class="list-avatar" :class="{ 'avatar-online': device.is_online }">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" v-html="deviceIcon"></svg>
    </div>
    <span class="list-name" @click="emit('edit', device)">{{ device.name }}</span>
    <span class="list-ip">{{ device.ip }}</span>
    <span class="list-mac">{{ device.mac }}</span>
    <span class="list-seen">{{ timeAgo(device.last_seen_at) }}</span>
    <div class="list-actions">
      <button class="list-action-btn wake" :disabled="device.is_online || waking" @click="handleWake" title="开机">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
      </button>
      <button class="list-action-btn shut" :disabled="!device.shutdown_enabled || shutting" @click="handleShutdown" title="关机">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><rect x="8" y="8" width="8" height="8" rx="1"/></svg>
      </button>
      <button class="list-action-btn edit" @click.stop="emit('edit', device)" title="编辑">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
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
  position: relative;
}
.device-card.batch-selected {
  border-color: rgba(0, 122, 255, 0.4);
  background: rgba(0, 122, 255, 0.04);
}

.batch-checkbox {
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.checkbox-inner {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 2px solid #c7c7cc;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.checkbox-inner.checked {
  background: #007AFF;
  border-color: #007AFF;
}

.edit-btn {
  background: none;
  border: none;
  color: #8e8e93;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  opacity: 0;
  flex-shrink: 0;
}
.device-card:hover .edit-btn {
  opacity: 1;
}
.edit-btn:hover {
  color: #007AFF;
  background: rgba(0, 122, 255, 0.08);
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

/* List mode */
.device-list-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255,255,255,0.95);
  transition: background 0.15s;
}
.device-list-row:hover {
  background: rgba(0,122,255,0.03);
}
.device-list-row.online {
  /* subtle left accent handled by dot */
}
.device-list-row.batch-selected {
  background: rgba(0, 122, 255, 0.06);
}
.list-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-online { background: #34C759; box-shadow: 0 0 6px rgba(52,199,89,0.4); }
.dot-offline { background: #c7c7cc; }
.list-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: #f2f2f7;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8e8e93;
  flex-shrink: 0;
}
.list-avatar.avatar-online {
  background: rgba(52,199,89,0.12);
  color: #34C759;
}
.list-name {
  font-weight: 600;
  font-size: 14px;
  color: #1c1c1e;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 100px;
  max-width: 160px;
  transition: color 0.2s;
}
.list-name:hover { color: #007AFF; }
.list-ip {
  font-size: 13px;
  color: #636366;
  white-space: nowrap;
  min-width: 110px;
}
.list-mac {
  font-size: 12px;
  color: #8e8e93;
  font-family: "SF Mono", "Menlo", monospace;
  white-space: nowrap;
  min-width: 130px;
}
.list-seen {
  font-size: 12px;
  color: #aeaeb2;
  white-space: nowrap;
  margin-left: auto;
  flex-shrink: 0;
}
.list-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.list-action-btn {
  border: none;
  background: none;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #8e8e93;
}
.list-action-btn:hover { background: rgba(0,0,0,0.04); }
.list-action-btn.wake { color: #007AFF; }
.list-action-btn.wake:hover { background: rgba(0,122,255,0.1); }
.list-action-btn.shut { color: #FF3B30; }
.list-action-btn.shut:hover { background: rgba(255,59,48,0.1); }
.list-action-btn.edit { color: #8e8e93; }
.list-action-btn.edit:hover { color: #007AFF; background: rgba(0,122,255,0.08); }
.list-action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.list-action-btn:disabled:hover { background: none; }
</style>
