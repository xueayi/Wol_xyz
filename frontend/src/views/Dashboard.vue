<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useAuthStore } from '../stores/auth'
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

const store = useDashboardStore()
const auth = useAuthStore()

const searchQuery = ref('')
const filterGroup = ref<number | null>(null)
const viewMode = ref<'card' | 'list'>('card')

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
    case 'wolConfig':
      infoTitle.value = 'WoL 配置指引'
      infoContent.value = `
        <h3>远程开机 (Wake-on-LAN)</h3>
        <h4>Windows</h4>
        <ol>
          <li><b>BIOS</b>：电源管理 → 启用 Wake on LAN / PCI-E 唤醒</li>
          <li><b>设备管理器</b>：网卡 → 属性 → 电源管理 → 勾选「允许此设备唤醒计算机」</li>
          <li><b>网卡高级属性</b>：启用「魔术封包唤醒」(Wake on Magic Packet)</li>
          <li><b>关闭快速启动</b>：控制面板 → 电源选项 → 关闭快速启动</li>
        </ol>
        <h4>Linux</h4>
        <ol>
          <li><b>BIOS</b>：同上，启用 Wake on LAN</li>
          <li><b>安装 ethtool</b>：<code>sudo apt install ethtool</code></li>
          <li><b>启用 WoL</b>：<code>sudo ethtool -s eth0 wol g</code>（eth0 替换为实际网卡名）</li>
          <li><b>持久化</b>：编辑 <code>/etc/network/interfaces</code> 或创建 systemd 服务使其开机生效</li>
        </ol>
        <h4>macOS</h4>
        <ol>
          <li>系统设置 → 节能 → 勾选「唤醒以供网络访问」</li>
          <li>仅支持有线以太网连接，Wi-Fi 下 WoL 不可用</li>
        </ol>
        <h3>远程关机 (SSH)</h3>
        <ol>
          <li><b>Windows</b>：设置 → 应用 → 可选功能 → 添加 OpenSSH Server</li>
          <li><b>Linux / macOS</b>：通常自带 SSH，确保 sshd 已启用</li>
          <li>确保 SSH 端口 22 未被防火墙阻止</li>
          <li>在设备设置中启用远程关机并填写 SSH 凭据</li>
        </ol>`
      showInfoModal.value = true
      break
    case 'guide':
      showGuideModal.value = true
      break
    case 'about':
      infoTitle.value = '项目说明'
      infoContent.value = `
        <h3>XiaoXue WoL — 局域网设备管理</h3>
        <p>一个轻量级的局域网设备远程管理工具，支持 Wake-on-LAN 远程开机、SSH 远程关机、设备状态监控、定时任务和多渠道通知。</p>
        <h3>核心功能</h3>
        <ul>
          <li>多设备管理与分组</li>
          <li>实时在线状态监控（ICMP Ping）</li>
          <li>WOL 远程开机 / SSH 远程关机</li>
          <li>定时任务（Cron 表达式）</li>
          <li>外部触发源（巴法云 / HTTP API / MQTT）</li>
          <li>通知渠道（邮件 / Webhook）</li>
          <li>操作日志记录</li>
        </ul>
        <p style="margin-top:12px"><a href="https://github.com/xueayi/XiaoXue_WoL" target="_blank" style="color:#007AFF;text-decoration:none;font-weight:500">GitHub 仓库 →</a></p>`
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
          <h1 class="app-title">XiaoXue WoL</h1>
          <p class="app-subtitle">局域网设备管理</p>
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
            @refresh="refresh"
            @edit-device="handleEditDevice"
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

@media (max-width: 1024px) {
  .main-content { grid-template-columns: 1fr; }
  .sidebar { order: -1; }
}
</style>
