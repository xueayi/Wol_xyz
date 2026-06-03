<script setup lang="ts">
import { ref, watch } from 'vue'
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
const form = ref({ name: '', device_id: null as number | null, action: 'wake', cron_expression: '', enabled: true })
const saving = ref(false)

watch(() => emit, loadData, { immediate: false })

async function loadData() {
  const [s, d] = await Promise.all([getSchedules(), getDevices()])
  schedules.value = s.data
  devices.value = d.data
}

function openAdd() {
  editItem.value = null
  form.value = { name: '', device_id: null, action: 'wake', cron_expression: '', enabled: true }
  showForm.value = true
}

function openEdit(item: any) {
  editItem.value = item
  form.value = { ...item }
  showForm.value = true
}

async function handleSave() {
  if (!form.value.name || !form.value.device_id || !form.value.cron_expression) {
    msg.warning('请填写完整信息')
    return
  }
  saving.value = true
  try {
    if (editItem.value) {
      await updateSchedule(editItem.value.id, form.value)
    } else {
      await createSchedule(form.value)
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
        <thead><tr><th>名称</th><th>设备</th><th>动作</th><th>Cron</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="s in schedules" :key="s.id">
            <td>{{ s.name }}</td>
            <td>{{ devices.find(d => d.id === s.device_id)?.name || s.device_id }}</td>
            <td>{{ s.action === 'wake' ? '开机' : '关机' }}</td>
            <td style="font-family:monospace;font-size:12px">{{ s.cron_expression }}</td>
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
        <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="设备">
          <n-select v-model:value="form.device_id" :options="deviceOptions()" placeholder="选择设备" />
        </n-form-item>
        <n-form-item label="动作">
          <n-radio-group v-model:value="form.action">
            <n-radio value="wake">开机</n-radio>
            <n-radio value="shutdown">关机</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="Cron">
          <n-input v-model:value="form.cron_expression" placeholder="分 时 日 月 星期  例: 0 8 * * 1-5" />
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
