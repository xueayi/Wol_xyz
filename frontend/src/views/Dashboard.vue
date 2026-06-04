<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useAuthStore } from '../stores/auth'
import { useMessage } from 'naive-ui'
import StatsBar from '../components/StatsBar.vue'
import DeviceGroup from '../components/DeviceGroup.vue'
import QuickActions from '../components/QuickActions.vue'
import ChannelStatus from '../components/ChannelStatus.vue'
import RecentLogs from '../components/RecentLogs.vue'
import DeviceModal from '../components/modals/DeviceModal.vue'
import ScanModal from '../components/modals/ScanModal.vue'
import ScheduleModal from '../components/modals/ScheduleModal.vue'
import ChannelModal from '../components/modals/ChannelModal.vue'
import LogsModal from '../components/modals/LogsModal.vue'
import InfoModal from '../components/modals/InfoModal.vue'
import GuideModal from '../components/modals/GuideModal.vue'
import TriggerModal from '../components/modals/TriggerModal.vue'
import GroupModal from '../components/modals/GroupModal.vue'
import UserModal from '../components/modals/UserModal.vue'
import { batchDeleteDevices, batchMoveDevices } from '../api/devices'
import { getGroups } from '../api/groups'

const store = useDashboardStore()
const auth = useAuthStore()
const msg = useMessage()

const searchQuery = ref('')
const filterGroup = ref<number | null>(null)
const viewMode = ref<'card' | 'list'>('card')

const batchMode = ref(false)
const selectedDevices = ref<number[]>([])
const batchGroups = ref<any[]>([])
const showBatchMoveSelect = ref(false)
const batchMoveTarget = ref<number | null>(null)

const showDeviceModal = ref(false)
const editingDevice = ref<any>(null)
const showScanModal = ref(false)
const showScheduleModal = ref(false)
const showChannelModal = ref(false)
const showLogsModal = ref(false)
const showGroupModal = ref(false)
const showInfoModal = ref(false)
const showGuideModal = ref(false)
const showTriggerModal = ref(false)
const showUserModal = ref(false)
const infoTitle = ref('')
const infoContent = ref('')

const filteredGroups = computed(() => {
  let groups = store.groups
  if (filterGroup.value !== null) {
    groups = groups.filter((g: any) => g.id === filterGroup.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    groups = groups.map((g: any) => ({
      ...g,
      devices: g.devices?.filter((d: any) =>
        d.name.toLowerCase().includes(q) ||
        d.ip.includes(q) ||
        d.mac.toLowerCase().includes(q)
      ),
    })).filter((g: any) => g.devices?.length > 0)
  }
  return groups
})

const groupOptions = computed(() => [
  { label: '全部分组', value: null },
  ...store.groups.map((g: any) => ({ label: g.name, value: g.id })),
])

let ws: WebSocket | null = null

function connectWs() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${location.host}/ws/status`)
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.type === 'device_status') {
      store.updateDeviceStatus(data.device_id, data.is_online)
    }
  }
  ws.onclose = () => setTimeout(connectWs, 3000)
}

function handleAction(key: string) {
  switch (key) {
    case 'scan': showScanModal.value = true; break
    case 'addDevice': editingDevice.value = null; showDeviceModal.value = true; break
    case 'schedules': showScheduleModal.value = true; break
    case 'triggers': showTriggerModal.value = true; break
    case 'userMgmt': showUserModal.value = true; break
    case 'guide': showGuideModal.value = true; break
    case 'about':
      infoTitle.value = '项目说明'
      infoContent.value = `
        <h3>Wol_xyz — 局域网设备管理</h3>
        <p>一个轻量级的局域网设备远程管理工具，支持 Wake-on-LAN 远程开机、SSH 远程关机、设备状态监控、定时任务和多渠道通知。</p>
        <h3>核心功能</h3>
        <ul>
          <li>多设备管理与分组</li>
          <li>实时在线状态监控（ICMP Ping）</li>
          <li>WOL 远程开机 / SSH 远程关机</li>
          <li>定时任务（Cron 表达式）</li>
          <li>外部触发源（巴法云 / API / MQTT / Telegram）</li>
          <li>通知渠道（邮件 / Webhook / Telegram）</li>
          <li>操作日志记录</li>
        </ul>
        <p style="margin-top:12px"><a href="https://github.com/xueayi/Wol_XYZ" target="_blank" style="color:#007AFF;text-decoration:none;font-weight:500">GitHub 仓库 →</a></p>`
      showInfoModal.value = true
      break
  }
}

function handleEditDevice(device: any) {
  editingDevice.value = device
  showDeviceModal.value = true
}

async function refresh() {
  await store.fetchAll()
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedDevices.value = []
    showBatchMoveSelect.value = false
  }
}

const allDeviceIds = computed(() => {
  const ids: number[] = []
  for (const g of filteredGroups.value) {
    if (g.devices) {
      for (const d of g.devices) ids.push(d.id)
    }
  }
  return ids
})

const isAllSelected = computed(() =>
  allDeviceIds.value.length > 0 && allDeviceIds.value.every((id) => selectedDevices.value.includes(id))
)

function selectAllDevices() {
  if (isAllSelected.value) {
    selectedDevices.value = []
  } else {
    selectedDevices.value = [...allDeviceIds.value]
  }
}

function toggleDeviceSelect(id: number) {
  const idx = selectedDevices.value.indexOf(id)
  if (idx === -1) selectedDevices.value.push(id)
  else selectedDevices.value.splice(idx, 1)
}

async function handleBatchDelete() {
  if (selectedDevices.value.length === 0) return
  try {
    await batchDeleteDevices(selectedDevices.value)
    msg.success(`已删除 ${selectedDevices.value.length} 台设备`)
    selectedDevices.value = []
    batchMode.value = false
    await refresh()
  } catch { msg.error('批量删除失败') }
}

async function openBatchMove() {
  const { data } = await getGroups()
  batchGroups.value = data
  showBatchMoveSelect.value = true
}

async function handleBatchMove() {
  if (selectedDevices.value.length === 0) return
  try {
    await batchMoveDevices(selectedDevices.value, batchMoveTarget.value)
    msg.success(`已移动 ${selectedDevices.value.length} 台设备`)
    selectedDevices.value = []
    batchMode.value = false
    showBatchMoveSelect.value = false
    await refresh()
  } catch { msg.error('批量移动失败') }
}

onMounted(async () => {
  await auth.fetchUser()
  await store.fetchAll()
  connectWs()
})

onUnmounted(() => { ws?.close() })
</script>

<template>
  <div class="dashboard">
    <div class="header">
      <div class="header-left">
        <div class="app-logo">
          <svg width="28" height="28" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#hg1)"/>
            <path d="M14 28V20a10 10 0 0120 0v8" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="24" cy="32" r="3" fill="#fff"/>
            <defs><linearGradient id="hg1" x1="0" y1="0" x2="48" y2="48"><stop stop-color="#007AFF"/><stop offset="1" stop-color="#5856D6"/></linearGradient></defs>
          </svg>
        </div>
        <div>
          <h1 class="app-title">Wol_xyz</h1>
          <p class="app-subtitle">局域网设备管理 <span v-if="store.stats.version" class="version-tag">v{{ store.stats.version }}</span></p>
        </div>
      </div>
      <div class="header-right">
        <span class="user-badge">{{ auth.user?.username }}</span>
        <button class="logout-btn" @click="auth.logout()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          退出
        </button>
      </div>
    </div>

    <StatsBar :stats="store.stats" />

    <div class="main-content">
      <div class="device-overview">
        <div class="overview-toolbar">
          <div class="toolbar-left">
            <h2>设备概览</h2>
            <n-select v-model:value="filterGroup" :options="groupOptions" size="small"
              style="width:130px" :consistent-menu-width="false" />
            <button class="text-btn" @click="showGroupModal = true">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              分组管理
            </button>
            <button class="text-btn" :class="{ 'text-btn-active': batchMode }" @click="toggleBatchMode">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
              {{ batchMode ? '退出批量' : '批量管理' }}
            </button>
          </div>
          <div class="toolbar-right">
            <div class="view-toggle">
              <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
              </button>
              <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
              </button>
            </div>
            <div class="search-box">
              <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8e8e93" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input v-model="searchQuery" placeholder="搜索设备名称、IP 或 MAC" />
            </div>
          </div>
        </div>

        <div v-if="store.loading" class="loading-state">
          <div class="spinner" />
          <span>加载中...</span>
        </div>
        <template v-else>
          <DeviceGroup
            v-for="group in filteredGroups"
            :key="group.id"
            :group="group"
            :view-mode="viewMode"
            :batch-mode="batchMode"
            :selected-devices="selectedDevices"
            @refresh="refresh"
            @edit-device="handleEditDevice"
            @toggle-select="toggleDeviceSelect"
          />
          <div v-if="filteredGroups.length === 0" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#c7c7cc" stroke-width="1.5" stroke-linecap="round">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            <p>暂无设备</p>
            <span>点击右侧「手动添加」或「扫描局域网」添加设备</span>
          </div>
        </template>
      </div>

      <div class="sidebar">
        <div class="sidebar-card"><QuickActions @action="handleAction" /></div>
        <div class="sidebar-card"><ChannelStatus :channels="store.channels" @add="showChannelModal = true" /></div>
        <div class="sidebar-card"><RecentLogs :logs="store.recentLogs" @view-all="showLogsModal = true" /></div>
      </div>
    </div>

    <DeviceModal v-model:show="showDeviceModal" :device="editingDevice" @saved="refresh" />
    <ScanModal v-model:show="showScanModal" @saved="refresh" />
    <ScheduleModal v-model:show="showScheduleModal" @saved="refresh" />
    <ChannelModal v-model:show="showChannelModal" @saved="refresh" />
    <LogsModal v-model:show="showLogsModal" />
    <GroupModal v-model:show="showGroupModal" @saved="refresh" />
    <InfoModal v-model:show="showInfoModal" :title="infoTitle" :content="infoContent" />
    <GuideModal v-model:show="showGuideModal" />
    <TriggerModal v-model:show="showTriggerModal" @saved="refresh" />
    <UserModal v-model:show="showUserModal" />

    <Transition name="slide-up">
      <div v-if="batchMode" class="batch-bar">
        <span class="batch-count">已选 {{ selectedDevices.length }} / {{ allDeviceIds.length }}</span>
        <div class="batch-actions">
          <button class="batch-btn" @click="selectAllDevices">{{ isAllSelected ? '取消全选' : '全选' }}</button>
          <n-popconfirm @positive-click="handleBatchDelete" :disabled="selectedDevices.length === 0">
            <template #trigger>
              <button class="batch-btn batch-btn-danger" :disabled="selectedDevices.length === 0">批量删除</button>
            </template>
            确定删除选中的 {{ selectedDevices.length }} 台设备？
          </n-popconfirm>
          <button class="batch-btn batch-btn-primary" :disabled="selectedDevices.length === 0" @click="openBatchMove">移动到分组</button>
          <button class="batch-btn" @click="toggleBatchMode">退出</button>
        </div>
      </div>
    </Transition>

    <n-modal v-model:show="showBatchMoveSelect" preset="card" title="移动到分组" style="width:380px" :bordered="false">
      <n-select v-model:value="batchMoveTarget" placeholder="选择目标分组（留空为取消分组）"
        :options="[{ label: '取消分组', value: null }, ...batchGroups.map((g: any) => ({ label: g.name, value: g.id }))]"
        clearable />
      <template #action>
        <n-button type="primary" @click="handleBatchMove">确定移动</n-button>
      </template>
    </n-modal>

    <footer class="app-footer">
      <span>Wol_xyz</span>
      <span v-if="store.stats.version" class="footer-version">v{{ store.stats.version }}</span>
      <span class="footer-sep">·</span>
      <a href="https://github.com/xueayi/Wol_XYZ" target="_blank" class="footer-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        GitHub
      </a>
    </footer>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 24px;
  min-height: 100vh;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.app-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1c1c1e;
  letter-spacing: -0.5px;
}
.app-subtitle {
  margin: 0;
  font-size: 12px;
  color: #8e8e93;
  font-weight: 500;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-badge {
  font-size: 13px;
  font-weight: 600;
  color: #636366;
  background: rgba(0,0,0,0.04);
  padding: 4px 12px;
  border-radius: 20px;
}
.logout-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: none;
  color: #8e8e93;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 8px;
  font-family: inherit;
  transition: all 0.2s;
}
.logout-btn:hover {
  background: rgba(0,0,0,0.04);
  color: #FF3B30;
}

/* Main layout */
.main-content {
  display: grid;
  grid-template-columns: 1fr 310px;
  gap: 20px;
  align-items: start;
}

/* Overview toolbar */
.overview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.toolbar-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1c1c1e;
  letter-spacing: -0.3px;
  white-space: nowrap;
}
.text-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: none;
  color: #007AFF;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  font-family: inherit;
  transition: background 0.2s;
}
.text-btn:hover { background: rgba(0,122,255,0.06); }
.text-btn-active {
  color: #FF3B30;
}
.text-btn-active:hover { background: rgba(255,59,48,0.06); }
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.view-toggle {
  display: flex;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  padding: 2px;
}
.view-toggle button {
  border: none;
  background: none;
  padding: 5px 8px;
  border-radius: 6px;
  cursor: pointer;
  color: #8e8e93;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}
.view-toggle button.active {
  background: #fff;
  color: #1c1c1e;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0,0,0,0.04);
  border-radius: 10px;
  padding: 7px 12px;
  width: 240px;
  transition: all 0.2s;
}
.search-box:focus-within {
  background: #fff;
  box-shadow: 0 0 0 2px rgba(0,122,255,0.2);
}
.search-box input {
  border: none;
  outline: none;
  background: none;
  font-size: 13px;
  color: #1c1c1e;
  width: 100%;
  font-family: inherit;
}
.search-box input::placeholder { color: #aeaeb2; }

/* States */
.loading-state {
  text-align: center;
  padding: 80px 0;
  color: #8e8e93;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.spinner {
  width: 24px;
  height: 24px;
  border: 2.5px solid rgba(0,0,0,0.06);
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #c7c7cc;
}
.empty-state p {
  margin: 16px 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: #8e8e93;
}
.empty-state span {
  font-size: 13px;
  color: #aeaeb2;
}

/* Sidebar */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sidebar-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 18px;
  border: 0.5px solid rgba(0,0,0,0.04);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.02);
}

.version-tag {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  color: #007AFF;
  background: rgba(0,122,255,0.1);
  padding: 1px 6px;
  border-radius: 6px;
  margin-left: 4px;
  vertical-align: middle;
}
.app-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 24px 0 12px;
  font-size: 12px;
  color: #c7c7cc;
}
.footer-version {
  font-family: 'SF Mono', SFMono-Regular, Menlo, monospace;
  font-size: 11px;
}
.footer-sep { color: #d1d1d6; }
.footer-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #8e8e93;
  text-decoration: none;
  transition: color 0.2s;
}
.footer-link:hover { color: #007AFF; }

@media (max-width: 1024px) {
  .main-content { grid-template-columns: 1fr; }
  .sidebar { order: -1; }
}

/* Batch action bar */
.batch-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12), 0 0 0 0.5px rgba(0,0,0,0.06);
  z-index: 100;
}
.batch-count {
  font-size: 14px;
  font-weight: 600;
  color: #1c1c1e;
  white-space: nowrap;
}
.batch-actions {
  display: flex;
  gap: 8px;
}
.batch-btn {
  border: none;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
  background: rgba(0,0,0,0.05);
  color: #636366;
}
.batch-btn:hover { background: rgba(0,0,0,0.08); }
.batch-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.batch-btn:disabled:hover { background: rgba(0,0,0,0.05); }
.batch-btn-primary {
  background: rgba(0,122,255,0.1);
  color: #007AFF;
}
.batch-btn-primary:hover { background: rgba(0,122,255,0.18); }
.batch-btn-danger {
  background: rgba(255,59,48,0.1);
  color: #FF3B30;
}
.batch-btn-danger:hover { background: rgba(255,59,48,0.18); }

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
