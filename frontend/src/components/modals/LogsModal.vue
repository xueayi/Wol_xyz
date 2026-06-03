<script setup lang="ts">
import { ref } from 'vue'
import { getLogs } from '../../api/misc'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show'])

const logs = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20

async function loadData() {
  loading.value = true
  try {
    const { data } = await getLogs({ limit: pageSize, offset: (page.value - 1) * pageSize })
    logs.value = data
  } finally { loading.value = false }
}

function formatTime(dt: string) {
  return new Date(dt).toLocaleString('zh-CN')
}

const actionLabels: Record<string, string> = { wake: '开机', shutdown: '关机', scan: '扫描' }
const sourceLabels: Record<string, string> = { manual: '手动', scheduled: '定时', external: '外部' }
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="操作日志" style="width: 800px" :bordered="false" @after-enter="loadData">
    <n-table :bordered="false" :single-line="false" size="small" :loading="loading">
      <thead>
        <tr><th>时间</th><th>设备</th><th>动作</th><th>结果</th><th>来源</th><th>详情</th></tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td style="white-space:nowrap;font-size:12px">{{ formatTime(log.created_at) }}</td>
          <td>{{ log.device_name || '-' }}</td>
          <td>{{ actionLabels[log.action] || log.action }}</td>
          <td>
            <n-tag :type="log.result === 'success' ? 'success' : 'error'" size="tiny">
              {{ log.result === 'success' ? '成功' : '失败' }}
            </n-tag>
          </td>
          <td>{{ sourceLabels[log.source] || log.source }}</td>
          <td style="font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ log.detail }}</td>
        </tr>
      </tbody>
    </n-table>
    <div style="display:flex;justify-content:center;margin-top:12px">
      <n-pagination v-model:page="page" :page-size="pageSize" @update:page="loadData" />
    </div>
  </n-modal>
</template>
