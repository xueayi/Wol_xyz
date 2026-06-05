<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { createDevice, updateDevice, deleteDevice } from '../../api/devices'
import { getGroups } from '../../api/groups'

const props = defineProps<{ show: boolean; device?: any }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

const form = ref<any>({})
const groups = ref<any[]>([])
const saving = ref(false)
const isEdit = ref(false)

const deviceTypeOptions = [
  { label: 'Windows', value: 'windows' },
  { label: 'macOS', value: 'macos' },
  { label: 'Linux', value: 'linux' },
  { label: 'iPhone', value: 'iphone' },
  { label: 'iPad', value: 'ipad' },
  { label: 'Android', value: 'android' },
  { label: '智能手表', value: 'watch' },
  { label: 'NAS', value: 'nas' },
  { label: '路由器', value: 'router' },
  { label: 'IoT 设备', value: 'iot' },
  { label: '其他电脑', value: 'computer' },
  { label: '其他设备', value: 'other' },
]

const shutdownCapableTypes = new Set(['windows', 'linux', 'macos'])
const canShutdown = computed(() => shutdownCapableTypes.has(form.value.device_type))

const authTypeOptions = [
  { label: '密码', value: 'password' },
  { label: '密钥', value: 'key' },
]

watch(() => props.show, async (v) => {
  if (!v) return
  const { data } = await getGroups()
  groups.value = data
  if (props.device) {
    isEdit.value = true
    form.value = { ...props.device }
  } else {
    isEdit.value = false
    form.value = { name: '', ip: '', mac: '', adapter_name: '', device_type: 'computer', group_id: null, shutdown_enabled: false, shutdown_user: '', shutdown_password: '', shutdown_auth_type: 'password', shutdown_private_key: '' }
  }
})

watch(() => form.value.device_type, () => {
  if (!canShutdown.value) {
    form.value.shutdown_enabled = false
  }
})

async function handleSave() {
  if (!form.value.name || !form.value.ip || !form.value.mac) {
    msg.warning('请填写名称、IP 和 MAC 地址')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await updateDevice(form.value.id, form.value)
      msg.success('设备已更新')
    } else {
      await createDevice(form.value)
      msg.success('设备已添加')
    }
    emit('saved')
    emit('update:show', false)
  } catch (e: any) {
    msg.error(e.response?.data?.detail || '操作失败')
  } finally { saving.value = false }
}

async function handleDelete() {
  if (!isEdit.value) return
  try {
    await deleteDevice(form.value.id)
    msg.success('设备已删除')
    emit('saved')
    emit('update:show', false)
  } catch { msg.error('删除失败') }
}

const groupOptions = () => groups.value.map((g: any) => ({ label: g.name, value: g.id }))
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    :title="isEdit ? '编辑设备' : '添加设备'" style="width: 500px" :bordered="false">
    <n-form label-placement="left" label-width="80">
      <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
      <n-form-item label="IP 地址"><n-input v-model:value="form.ip" placeholder="192.168.1.100" /></n-form-item>
      <n-form-item label="MAC 地址"><n-input v-model:value="form.mac" placeholder="AA:BB:CC:DD:EE:FF" /></n-form-item>
      <n-form-item label="设备类型">
        <n-select v-model:value="form.device_type" :options="deviceTypeOptions" />
      </n-form-item>
      <n-form-item label="网卡名称"><n-input v-model:value="form.adapter_name" placeholder="可选" /></n-form-item>
      <n-form-item label="分组">
        <n-select v-model:value="form.group_id" :options="groupOptions()" clearable placeholder="选择分组" />
      </n-form-item>
      <n-divider />
      <n-form-item label="远程关机">
        <n-switch v-model:value="form.shutdown_enabled" :disabled="!canShutdown" />
        <span v-if="!canShutdown" style="margin-left:8px;font-size:12px;color:var(--n-text-color-3)">仅 Windows / Linux / macOS 设备支持</span>
      </n-form-item>
      <template v-if="form.shutdown_enabled">
        <n-form-item label="SSH 用户名"><n-input v-model:value="form.shutdown_user" /></n-form-item>
        <n-form-item label="认证方式">
          <n-radio-group v-model:value="form.shutdown_auth_type">
            <n-radio-button v-for="o in authTypeOptions" :key="o.value" :value="o.value" :label="o.label" />
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="form.shutdown_auth_type === 'password'" label="SSH 密码">
          <n-input v-model:value="form.shutdown_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item v-if="form.shutdown_auth_type === 'key'" label="SSH 私钥">
          <n-input v-model:value="form.shutdown_private_key" type="textarea" :rows="4" placeholder="粘贴 SSH 私钥内容（PEM 格式）" />
        </n-form-item>
      </template>
    </n-form>
    <template #action>
      <div style="display:flex;gap:8px;width:100%">
        <n-button v-if="isEdit" type="error" ghost @click="handleDelete">删除</n-button>
        <div style="flex:1" />
        <n-button @click="emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
      </div>
    </template>
  </n-modal>
</template>
