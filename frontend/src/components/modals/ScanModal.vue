<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { scanLan } from '../../api/misc'
import { createDevice } from '../../api/devices'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

const scanning = ref(false)
const results = ref<any[]>([])
const existingMacs = ref<string[]>([])
const selected = ref<string[]>([])

const typeLabels: Record<string, string> = {
  windows: 'Windows',
  macos: 'macOS/Apple',
  linux: 'Linux',
  iphone: 'iPhone',
  ipad: 'iPad',
  android: 'Android',
  watch: '手表',
  nas: 'NAS',
  router: '路由器',
  iot: 'IoT',
  computer: '电脑',
  other: '其他',
}

const nonWolTypes = ['iphone', 'ipad', 'android', 'watch', 'iot', 'other']

function isNonWol(type: string) {
  return nonWolTypes.includes(type)
}

const newDevices = computed(() => results.value.filter((d) => !existingMacs.value.includes(d.mac)))
const existingDevices = computed(() => results.value.filter((d) => existingMacs.value.includes(d.mac)))

async function handleScan() {
  scanning.value = true
  results.value = []
  existingMacs.value = []
  selected.value = []
  try {
    const { data } = await scanLan()
    results.value = data.devices || []
    existingMacs.value = data.existing_macs || []
    if (results.value.length === 0) msg.info('未发现设备')
    else if (newDevices.value.length === 0) msg.info('所有设备均已添加')
  } catch (e: any) {
    if (e?.response?.status === 409) msg.warning('扫描正在进行中，请稍候再试')
    else msg.error('扫描失败')
  } finally { scanning.value = false }
}

function selectAllNew() {
  selected.value = newDevices.value.map((d) => d.mac)
}

function clearSelection() {
  selected.value = []
}

async function addSelected() {
  let added = 0
  for (const mac of selected.value) {
    const dev = results.value.find((d) => d.mac === mac)
    if (dev) {
      try {
        const name = dev.hostname || `设备-${dev.ip.split('.').pop()}`
        await createDevice({
          name,
          ip: dev.ip,
          mac: dev.mac,
          device_type: dev.guessed_type || 'computer',
        })
        added++
      } catch { /* skip duplicates */ }
    }
  }
  msg.success(`已添加 ${added} 台设备`)
  emit('saved')
  emit('update:show', false)
}
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="扫描局域网" style="width: 780px" :bordered="false">
    <n-button type="primary" :loading="scanning" @click="handleScan" block>
      {{ scanning ? '正在扫描...' : '开始扫描' }}
    </n-button>
    <div v-if="results.length" style="margin-top:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
        <span style="font-size:13px;color:#636366">
          发现 {{ results.length }} 台设备，{{ newDevices.length }} 台可添加
        </span>
        <n-space size="small">
          <n-button size="tiny" @click="selectAllNew" :disabled="newDevices.length === 0">全选新设备</n-button>
          <n-button size="tiny" @click="clearSelection" :disabled="selected.length === 0">清除选择</n-button>
        </n-space>
      </div>
      <n-checkbox-group v-model:value="selected">
        <n-table :bordered="false" :single-line="false" size="small">
          <thead><tr><th style="width:40px"></th><th>设备名</th><th>IP</th><th>MAC</th><th>识别类型</th><th style="width:60px">状态</th></tr></thead>
          <tbody>
            <tr v-for="d in newDevices" :key="d.mac">
              <td><n-checkbox :value="d.mac" /></td>
              <td style="font-weight:500">{{ d.hostname || '-' }}</td>
              <td>{{ d.ip }}</td>
              <td style="font-family:monospace;font-size:12px">{{ d.mac }}</td>
              <td>
                <span>{{ typeLabels[d.guessed_type] || '电脑' }}</span>
                <n-tag v-if="isNonWol(d.guessed_type)" size="tiny" type="warning" style="margin-left:4px">非 WoL</n-tag>
              </td>
              <td></td>
            </tr>
            <tr v-for="d in existingDevices" :key="d.mac" style="opacity:0.5">
              <td><n-checkbox :value="d.mac" disabled /></td>
              <td style="font-weight:500">{{ d.hostname || '-' }}</td>
              <td>{{ d.ip }}</td>
              <td style="font-family:monospace;font-size:12px">{{ d.mac }}</td>
              <td>{{ typeLabels[d.guessed_type] || '电脑' }}</td>
              <td><n-tag size="tiny" type="info">已添加</n-tag></td>
            </tr>
          </tbody>
        </n-table>
      </n-checkbox-group>
    </div>
    <template #action>
      <n-button type="primary" :disabled="selected.length === 0" @click="addSelected">
        添加选中（{{ selected.length }}）
      </n-button>
    </template>
  </n-modal>
</template>
