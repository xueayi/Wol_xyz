<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { createDevice, updateDevice, deleteDevice, generateKeypair } from '../../api/devices'
import { getGroups } from '../../api/groups'

const props = defineProps<{ show: boolean; device?: any }>()
const emit = defineEmits(['update:show', 'saved', 'open-guide'])
const msg = useMessage()

const form = ref<any>({})
const groups = ref<any[]>([])
const saving = ref(false)
const isEdit = ref(false)
const generatingKey = ref(false)
const showPublicKey = ref(false)
const generatedPublicKey = ref('')

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

const hasExistingPassword = computed(() => isEdit.value && props.device?.has_password)
const hasExistingKey = computed(() => isEdit.value && props.device?.has_private_key)

function resetForm() {
  showPublicKey.value = false
  generatedPublicKey.value = ''
  copyFailed.value = false
}

watch(() => props.show, async (v) => {
  if (!v) { resetForm(); return }
  const { data } = await getGroups()
  groups.value = data
  if (props.device) {
    isEdit.value = true
    form.value = { ...props.device }
    form.value.shutdown_password = ''
    form.value.shutdown_private_key = ''
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
    const payload = { ...form.value }
    delete payload.has_password
    delete payload.has_private_key
    delete payload.is_online
    delete payload.last_seen_at
    delete payload.created_at
    delete payload.updated_at
    if (isEdit.value && !payload.shutdown_password?.trim()) delete payload.shutdown_password
    if (isEdit.value && !payload.shutdown_private_key?.trim()) delete payload.shutdown_private_key
    if (isEdit.value) {
      await updateDevice(form.value.id, payload)
      msg.success('设备已更新')
    } else {
      await createDevice(payload)
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

async function handleGenerateKey() {
  generatingKey.value = true
  try {
    const { data } = await generateKeypair()
    form.value.shutdown_private_key = data.private_key
    generatedPublicKey.value = data.public_key
    showPublicKey.value = true
    msg.success('密钥对已生成，私钥已自动填入')
  } catch { msg.error('生成密钥对失败') }
  finally { generatingKey.value = false }
}

const copyFailed = ref(false)

async function copyPublicKey() {
  const text = generatedPublicKey.value
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      msg.success('公钥已复制到剪贴板')
      return
    }
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;left:-9999px'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    if (ok) {
      msg.success('公钥已复制到剪贴板')
    } else {
      copyFailed.value = true
      msg.warning('自动复制不可用，请手动选择复制')
    }
  } catch {
    copyFailed.value = true
    msg.warning('自动复制不可用，请手动选择复制')
  }
}

const groupOptions = () => groups.value.map((g: any) => ({ label: g.name, value: g.id }))
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    :title="isEdit ? '编辑设备' : '添加设备'" style="width: 500px" :bordered="false">
    <n-form label-placement="left" label-width="90" class="device-form">
      <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
      <n-form-item label="IP 地址"><n-input v-model:value="form.ip" placeholder="192.168.1.100" /></n-form-item>
      <n-form-item label="MAC 地址"><n-input v-model:value="form.mac" placeholder="AA:BB:CC:DD:EE:FF" /></n-form-item>
      <n-form-item label="设备类型">
        <n-select v-model:value="form.device_type" :options="deviceTypeOptions" />
      </n-form-item>
      <n-form-item label="分组">
        <n-select v-model:value="form.group_id" :options="groupOptions()" clearable placeholder="选择分组" />
      </n-form-item>
      <n-divider />
      <n-form-item label="远程关机">
        <div style="display:flex;align-items:center;gap:8px;width:100%">
          <n-switch v-model:value="form.shutdown_enabled" :disabled="!canShutdown" />
          <span v-if="!canShutdown" style="font-size:12px;color:var(--n-text-color-3)">仅 Windows / Linux / macOS 设备支持</span>
        </div>
      </n-form-item>
      <template v-if="form.shutdown_enabled">
        <n-form-item label="SSH 用户名">
          <n-input v-model:value="form.shutdown_user" placeholder="目标设备的登录用户名" style="flex:1" />
        </n-form-item>
        <n-form-item label="认证方式">
          <n-radio-group v-model:value="form.shutdown_auth_type">
            <n-radio-button v-for="o in authTypeOptions" :key="o.value" :value="o.value" :label="o.label" />
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="form.shutdown_auth_type === 'password'" label="SSH 密码">
          <n-input v-model:value="form.shutdown_password" type="password" show-password-on="click"
            :placeholder="hasExistingPassword ? '•••••••• 已配置，输入新密码可覆盖' : '输入 SSH 密码'" />
        </n-form-item>
        <template v-if="form.shutdown_auth_type === 'key'">
          <n-form-item label="SSH 私钥">
            <div style="width:100%">
              <div v-if="hasExistingKey && !form.shutdown_private_key && !showPublicKey" class="cred-mask-block">
                <span>•••••••• 已配置</span>
              </div>
              <n-input v-else v-model:value="form.shutdown_private_key" type="textarea" :rows="4"
                :placeholder="hasExistingKey ? '已配置，留空保持不变。也可粘贴新私钥或点击下方生成' : '粘贴 PEM 格式私钥，或点击下方按钮一键生成'" />
              <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
                <n-button size="small" :loading="generatingKey" @click="handleGenerateKey">
                  生成密钥对
                </n-button>
                <n-button v-if="hasExistingKey && !form.shutdown_private_key && !showPublicKey" size="small" quaternary @click="form.shutdown_private_key = ' '">
                  手动修改
                </n-button>
                <span style="font-size:11px;color:#999">生成后需将公钥部署到目标设备才能认证</span>
              </div>
            </div>
          </n-form-item>
          <div v-if="showPublicKey" class="pubkey-box">
            <div class="pubkey-header">
              <span class="pubkey-label">公钥（复制后添加到目标设备的 authorized_keys）</span>
              <n-button size="tiny" quaternary type="primary" @click="copyPublicKey">复制</n-button>
            </div>
            <code class="pubkey-text" :class="{ selectable: copyFailed }" @click="copyFailed && ($event.target as HTMLElement)?.ownerDocument?.getSelection()?.selectAllChildren($event.target as Node)">{{ generatedPublicKey }}</code>
            <p v-if="copyFailed" class="pubkey-copy-tip">当前环境不支持自动复制（HTTP 非安全上下文），请手动选中上方公钥后 Ctrl+C / Cmd+C 复制</p>
            <p class="pubkey-hint">
              Linux/macOS: <code>echo "公钥" >> ~/.ssh/authorized_keys</code><br/>
              Windows 管理员: <code>Add-Content C:\ProgramData\ssh\administrators_authorized_keys "公钥"</code>
            </p>
          </div>
        </template>
        <div class="shutdown-guide-inline">
          <n-alert type="info" :show-icon="false" style="font-size:13px">
            <b>配置步骤：</b>① 确保目标设备已开启 SSH → ② 填写用户名和认证凭据 → ③ 保存后测试关机
            <br/>
            <span class="guide-link" @click="emit('open-guide', 'wol')">查看详细配置说明</span>
          </n-alert>
        </div>
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

<style scoped>
.device-form :deep(.n-form-item-label) {
  white-space: nowrap;
}
.guide-link {
  font-size: 12px;
  color: #007AFF;
  cursor: pointer;
  white-space: nowrap;
}
.guide-link:hover { text-decoration: underline; }
.pubkey-box {
  background: rgba(0, 122, 255, 0.04);
  border: 1px solid rgba(0, 122, 255, 0.15);
  border-radius: 10px;
  padding: 10px 14px;
  margin: -8px 0 8px 90px;
}
.pubkey-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.pubkey-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}
.pubkey-text {
  font-size: 11px;
  word-break: break-all;
  color: #1c1c1e;
  font-family: 'SF Mono', SFMono-Regular, Menlo, monospace;
  line-height: 1.5;
  display: block;
}
.pubkey-hint {
  font-size: 11px;
  color: #999;
  margin: 6px 0 0;
  line-height: 1.6;
}
.pubkey-hint code {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 10px;
}
.pubkey-text.selectable {
  cursor: text;
  user-select: all;
  -webkit-user-select: all;
}
.pubkey-copy-tip {
  font-size: 11px;
  color: #e67e22;
  margin: 4px 0 0;
  line-height: 1.5;
}
.shutdown-guide-inline {
  margin: 4px 0 0;
}
.cred-mask-block {
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  padding: 10px 14px;
  font-family: 'SF Mono', SFMono-Regular, Menlo, monospace;
  font-size: 14px;
  color: #666;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
}
</style>
