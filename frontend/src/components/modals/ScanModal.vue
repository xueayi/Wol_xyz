<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { scanLan } from '../../api/misc'
import { createDevice } from '../../api/devices'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

const scanning = ref(false)
const results = ref<any[]>([])
const selected = ref<string[]>([])

async function handleScan() {
  scanning.value = true
  results.value = []
  try {
    const { data } = await scanLan()
    results.value = data.devices || []
    if (results.value.length === 0) msg.info('未发现新设备')
  } catch { msg.error('扫描失败') }
  finally { scanning.value = false }
}

async function addSelected() {
  for (const mac of selected.value) {
    const dev = results.value.find((d) => d.mac === mac)
    if (dev) {
      try {
        await createDevice({ name: `设备-${dev.ip.split('.').pop()}`, ip: dev.ip, mac: dev.mac })
      } catch { /* skip duplicates */ }
    }
  }
  msg.success(`已添加 ${selected.value.length} 台设备`)
  emit('saved')
  emit('update:show', false)
}
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="扫描局域网" style="width: 560px" :bordered="false">
    <n-button type="primary" :loading="scanning" @click="handleScan" block>
      {{ scanning ? '正在扫描...' : '开始扫描' }}
    </n-button>
    <div v-if="results.length" style="margin-top:16px">
      <n-checkbox-group v-model:value="selected">
        <n-table :bordered="false" :single-line="false" size="small">
          <thead><tr><th style="width:40px"></th><th>IP</th><th>MAC</th></tr></thead>
          <tbody>
            <tr v-for="d in results" :key="d.mac">
              <td><n-checkbox :value="d.mac" /></td>
              <td>{{ d.ip }}</td>
              <td style="font-family:monospace">{{ d.mac }}</td>
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
