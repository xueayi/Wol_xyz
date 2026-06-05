import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDashboardStats, getLogs } from '../api/misc'
import { getGroupsWithDevices } from '../api/groups'
import { getChannels } from '../api/channels'
import { getTriggers, getTriggerStatus } from '../api/triggers'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref({ total_devices: 0, online_devices: 0, group_count: 0, schedule_count: 0, today_triggers: 0, version: '' })
  const groups = ref<any[]>([])
  const recentLogs = ref<any[]>([])
  const channels = ref<any[]>([])
  const triggers = ref<any[]>([])
  const triggerStatus = ref<Record<string, string>>({})
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const [s, g, l, c, t, ts] = await Promise.all([
        getDashboardStats(),
        getGroupsWithDevices(),
        getLogs({ limit: 10 }),
        getChannels(),
        getTriggers(),
        getTriggerStatus(),
      ])
      stats.value = s.data
      groups.value = g.data
      recentLogs.value = l.data
      channels.value = c.data
      triggers.value = t.data
      triggerStatus.value = ts.data
    } finally {
      loading.value = false
    }
  }

  function updateDeviceStatus(deviceId: number, isOnline: boolean) {
    for (const g of groups.value) {
      const d = g.devices?.find((d: any) => d.id === deviceId)
      if (d) {
        d.is_online = isOnline
        break
      }
    }
    const online = groups.value.reduce((sum: number, g: any) =>
      sum + (g.devices?.filter((d: any) => d.is_online).length || 0), 0)
    stats.value.online_devices = online
  }

  return { stats, groups, recentLogs, channels, triggers, triggerStatus, loading, fetchAll, updateDeviceStatus }
})
