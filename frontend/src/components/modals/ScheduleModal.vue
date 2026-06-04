<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { getSchedules, createSchedule, updateSchedule, deleteSchedule } from '../../api/schedules'
import { getDevices } from '../../api/devices'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

const schedules = ref<any[]>([])
const devices = ref<any[]>([])
const showForm = ref(false)
const editItem = ref<any>(null)
const form = ref({
  name: '',
  device_id: null as number | null,
  action: 'wake',
  enabled: true,
})
const scheduleType = ref<'daily' | 'weekly' | 'monthly'>('daily')
const scheduleTime = ref<number>(Date.now())
const weekDays = ref<number[]>([])
const monthDay = ref<number>(1)
const saving = ref(false)

const weekDayOptions = [
  { label: '一', value: 1 },
  { label: '二', value: 2 },
  { label: '三', value: 3 },
  { label: '四', value: 4 },
  { label: '五', value: 5 },
  { label: '六', value: 6 },
  { label: '日', value: 0 },
]

const monthDayOptions = computed(() =>
  Array.from({ length: 31 }, (_, i) => ({ label: `${i + 1}日`, value: i + 1 }))
)

function cronToSchedule(cron: string) {
  const parts = cron.trim().split(/\s+/)
  if (parts.length < 5) return
  const [minute, hour, day, , weekday] = parts

  const d = new Date()
  d.setHours(parseInt(hour) || 0, parseInt(minute) || 0, 0, 0)
  scheduleTime.value = d.getTime()

  if (weekday !== '*' && day === '*') {
    scheduleType.value = 'weekly'
    weekDays.value = weekday.split(',').map((w) => parseInt(w))
  } else if (day !== '*') {
    scheduleType.value = 'monthly'
    monthDay.value = parseInt(day) || 1
  } else {
    scheduleType.value = 'daily'
  }
}

function scheduleToCron(): string {
  const d = new Date(scheduleTime.value)
  const minute = d.getMinutes()
  const hour = d.getHours()

  if (scheduleType.value === 'daily') {
    return `${minute} ${hour} * * *`
  } else if (scheduleType.value === 'weekly') {
    const days = weekDays.value.length > 0 ? weekDays.value.sort().join(',') : '*'
    return `${minute} ${hour} * * ${days}`
  } else {
    return `${minute} ${hour} ${monthDay.value} * *`
  }
}

function describeSchedule(cron: string): string {
  const parts = cron.trim().split(/\s+/)
  if (parts.length < 5) return cron
  const [minute, hour, day, , weekday] = parts
  const time = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`
  const dayNames = ['日', '一', '二', '三', '四', '五', '六']
  if (weekday !== '*' && day === '*') {
    const days = weekday.split(',').map((w) => `周${dayNames[parseInt(w)] || w}`).join('、')
    return `每${days} ${time}`
  } else if (day !== '*') {
    return `每月${day}日 ${time}`
  }
  return `每天 ${time}`
}

watch(() => emit, loadData, { immediate: false })

async function loadData() {
  const [s, d] = await Promise.all([getSchedules(), getDevices()])
  schedules.value = s.data
  devices.value = d.data
}

function openAdd() {
  editItem.value = null
  form.value = { name: '', device_id: null, action: 'wake', enabled: true }
  scheduleType.value = 'daily'
  const d = new Date()
  d.setHours(8, 0, 0, 0)
  scheduleTime.value = d.getTime()
  weekDays.value = []
  monthDay.value = 1
  showForm.value = true
}

function openEdit(item: any) {
  editItem.value = item
  form.value = { name: item.name, device_id: item.device_id, action: item.action, enabled: item.enabled }
  cronToSchedule(item.cron_expression)
  showForm.value = true
}

async function handleSave() {
  if (!form.value.name || !form.value.device_id) {
    msg.warning('请填写完整信息')
    return
  }
  if (scheduleType.value === 'weekly' && weekDays.value.length === 0) {
    msg.warning('请选择至少一天')
    return
  }
  saving.value = true
  try {
    const payload = { ...form.value, cron_expression: scheduleToCron() }
    if (editItem.value) {
      await updateSchedule(editItem.value.id, payload)
    } else {
      await createSchedule(payload)
    }
    showForm.value = false
    await loadData()
    emit('saved')
  } catch (e: any) { msg.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleDelete(id: number) {
  await deleteSchedule(id)
  await loadData()
  emit('saved')
}

const deviceOptions = () => devices.value.map((d: any) => ({ label: d.name, value: d.id }))
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="定时任务管理" style="width: 640px" :bordered="false" @after-enter="loadData">
    <template v-if="!showForm">
      <n-button type="primary" size="small" @click="openAdd" style="margin-bottom:12px">新建任务</n-button>
      <n-table :bordered="false" :single-line="false" size="small">
        <thead><tr><th>名称</th><th>设备</th><th>动作</th><th>执行时间</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="s in schedules" :key="s.id">
            <td>{{ s.name }}</td>
            <td>{{ devices.find(d => d.id === s.device_id)?.name || s.device_id }}</td>
            <td>{{ s.action === 'wake' ? '开机' : '关机' }}</td>
            <td style="font-size:13px">{{ describeSchedule(s.cron_expression) }}</td>
            <td><n-tag :type="s.enabled ? 'success' : 'default'" size="tiny">{{ s.enabled ? '启用' : '停用' }}</n-tag></td>
            <td>
              <n-button text size="tiny" @click="openEdit(s)">编辑</n-button>
              <n-popconfirm @positive-click="handleDelete(s.id)">
                <template #trigger><n-button text size="tiny" type="error">删除</n-button></template>
                确定删除此任务？
              </n-popconfirm>
            </td>
          </tr>
        </tbody>
      </n-table>
    </template>
    <template v-else>
      <n-form label-placement="left" label-width="80">
        <n-form-item label="名称"><n-input v-model:value="form.name" placeholder="例如：工作日开机" /></n-form-item>
        <n-form-item label="设备">
          <n-select v-model:value="form.device_id" :options="deviceOptions()" placeholder="选择设备" />
        </n-form-item>
        <n-form-item label="动作">
          <n-radio-group v-model:value="form.action">
            <n-radio value="wake">开机</n-radio>
            <n-radio value="shutdown">关机</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="频率">
          <n-radio-group v-model:value="scheduleType">
            <n-radio-button value="daily">每天</n-radio-button>
            <n-radio-button value="weekly">每周</n-radio-button>
            <n-radio-button value="monthly">每月</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="scheduleType === 'weekly'" label="周几">
          <n-checkbox-group v-model:value="weekDays">
            <n-space>
              <n-checkbox v-for="opt in weekDayOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item v-if="scheduleType === 'monthly'" label="日期">
          <n-select v-model:value="monthDay" :options="monthDayOptions" style="width: 120px" />
        </n-form-item>
        <n-form-item label="时间">
          <n-time-picker v-model:value="scheduleTime" format="HH:mm" :actions="[]" style="width: 140px" />
        </n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>
      </n-form>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <n-button @click="showForm = false">返回</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
      </div>
    </template>
  </n-modal>
</template>
