<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { getChannels, createChannel, updateChannel, deleteChannel, testChannel } from '../../api/channels'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

watch(() => props.show, (val) => {
  if (val) showForm.value = false
})

const channels = ref<any[]>([])
const showForm = ref(false)
const editItem = ref<any>(null)
const form = ref({ type: 'webhook', name: '', config: {} as any, enabled: true, notify_on_trigger: true, notify_on_success: false })
const saving = ref(false)
const testing = ref<number | null>(null)

const webhookPresets: Record<string, { label: string; url_hint: string; headers: Record<string, string>; body: string }> = {
  custom: { label: '自定义', url_hint: 'https://...', headers: { 'Content-Type': 'application/json' }, body: '{\n  "title": "{title}",\n  "body": "{body}"\n}' },
  feishu: { label: '飞书', url_hint: 'https://open.feishu.cn/open-apis/bot/v2/hook/xxx', headers: {}, body: '{\n  "msg_type": "text",\n  "content": {\n    "text": "{title}\\n{body}"\n  }\n}' },
  wechat: { label: '企业微信', url_hint: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx', headers: {}, body: '{\n  "msgtype": "text",\n  "text": {\n    "content": "{title}\\n{body}"\n  }\n}' },
}

const selectedPreset = ref('custom')
const showHeaderEditor = computed(() => selectedPreset.value === 'custom')

async function loadData() {
  const { data } = await getChannels()
  channels.value = data
}

function openAdd(type: string) {
  editItem.value = null
  if (type === 'email') {
    form.value = { type, name: '', config: { host: '', port: 587, tls: true, username: '', password: '', from_addr: '', to_addr: '' }, enabled: true, notify_on_trigger: true, notify_on_success: false }
  } else if (type === 'telegram') {
    form.value = { type, name: '', config: { bot_token: '', chat_ids: '' }, enabled: true, notify_on_trigger: true, notify_on_success: false }
  } else {
    selectedPreset.value = 'custom'
    const p = webhookPresets.custom
    form.value = { type, name: '', config: { url: '', method: 'POST', headers: JSON.stringify(p.headers, null, 2), body_template: p.body }, enabled: true, notify_on_trigger: true, notify_on_success: false }
  }
  showForm.value = true
}

function openEdit(item: any) {
  editItem.value = item
  if (item.type === 'webhook') {
    const cfg = { ...item.config }
    if (typeof cfg.headers === 'object') cfg.headers = JSON.stringify(cfg.headers, null, 2)
    if (typeof cfg.body_template === 'object') cfg.body_template = JSON.stringify(cfg.body_template, null, 2)
    selectedPreset.value = cfg._preset || 'custom'
    form.value = { type: item.type, name: item.name, config: cfg, enabled: item.enabled, notify_on_trigger: item.notify_on_trigger ?? true, notify_on_success: item.notify_on_success ?? false }
  } else {
    form.value = { type: item.type, name: item.name, config: { ...item.config }, enabled: item.enabled, notify_on_trigger: item.notify_on_trigger ?? true, notify_on_success: item.notify_on_success ?? false }
  }
  showForm.value = true
}

function applyPreset(preset: string) {
  selectedPreset.value = preset
  const p = webhookPresets[preset]
  if (!p) return
  form.value.config.headers = JSON.stringify(p.headers, null, 2)
  form.value.config.body_template = p.body
  if (!form.value.config.url) form.value.config.url = ''
}

async function handleSave() {
  saving.value = true
  try {
    const payload = { ...form.value }
    if (payload.type === 'webhook') {
      const cfg = { ...payload.config }
      try { cfg.headers = JSON.parse(cfg.headers) } catch { cfg.headers = {} }
      cfg._preset = selectedPreset.value
      try { cfg.body_template = JSON.parse(cfg.body_template) } catch { /* keep as string */ }
      payload.config = cfg
    }
    if (editItem.value) await updateChannel(editItem.value.id, payload)
    else await createChannel(payload)
    showForm.value = false
    await loadData()
    emit('saved')
  } catch (e: any) { msg.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleTest(id: number) {
  testing.value = id
  try {
    const { data } = await testChannel(id)
    data.success ? msg.success('测试通知已发送') : msg.error('发送失败')
  } catch { msg.error('测试失败') }
  finally { testing.value = null }
}

async function handleDelete(id: number) {
  await deleteChannel(id)
  await loadData()
  emit('saved')
}
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="通知渠道管理" style="width: 680px" :bordered="false" @after-enter="loadData">
    <template v-if="!showForm">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <n-button size="small" tertiary @click="openAdd('email')">+ 邮件</n-button>
        <n-button size="small" tertiary @click="openAdd('webhook')">+ Webhook</n-button>
        <n-button size="small" tertiary @click="openAdd('telegram')">+ Telegram</n-button>
      </div>
      <n-table :bordered="false" :single-line="false" size="small">
        <thead><tr><th>名称</th><th>类型</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="ch in channels" :key="ch.id">
            <td>{{ ch.name }}</td>
            <td>{{ { email: '邮件', webhook: 'Webhook', telegram: 'Telegram' }[ch.type] || ch.type }}</td>
            <td><n-tag :type="ch.enabled ? 'success' : 'default'" size="tiny">{{ ch.enabled ? '启用' : '禁用' }}</n-tag></td>
            <td style="display:flex;gap:4px">
              <n-button text size="tiny" @click="handleTest(ch.id)" :loading="testing === ch.id">测试</n-button>
              <n-button text size="tiny" @click="openEdit(ch)">编辑</n-button>
              <n-popconfirm @positive-click="handleDelete(ch.id)">
                <template #trigger><n-button text size="tiny" type="error">删除</n-button></template>
                确定删除此渠道？
              </n-popconfirm>
            </td>
          </tr>
        </tbody>
      </n-table>
    </template>
    <template v-else>
      <n-form label-placement="left" label-width="80">
        <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>
        <n-form-item label="触发通知">
          <n-switch v-model:value="form.notify_on_trigger" />
          <span style="margin-left:8px;font-size:12px;color:#999">发送开机/关机命令时通知</span>
        </n-form-item>
        <n-form-item label="成功通知">
          <n-switch v-model:value="form.notify_on_success" />
          <span style="margin-left:8px;font-size:12px;color:#999">设备确认开机/关机成功后通知</span>
        </n-form-item>
        <n-divider>{{ { email: '邮件配置', webhook: 'Webhook 配置', telegram: 'Telegram 配置' }[form.type] }}</n-divider>
        <template v-if="form.type === 'email'">
          <n-form-item label="SMTP"><n-input v-model:value="form.config.host" placeholder="smtp.example.com" /></n-form-item>
          <n-form-item label="端口"><n-input-number v-model:value="form.config.port" /></n-form-item>
          <n-form-item label="TLS"><n-switch v-model:value="form.config.tls" /></n-form-item>
          <n-form-item label="用户名"><n-input v-model:value="form.config.username" /></n-form-item>
          <n-form-item label="密码"><n-input v-model:value="form.config.password" type="password" show-password-on="click" /></n-form-item>
          <n-form-item label="发件人"><n-input v-model:value="form.config.from_addr" /></n-form-item>
          <n-form-item label="收件人"><n-input v-model:value="form.config.to_addr" /></n-form-item>
        </template>
        <template v-else-if="form.type === 'telegram'">
          <n-form-item label="Bot Token"><n-input v-model:value="form.config.bot_token" placeholder="从 @BotFather 获取" style="font-family:monospace" /></n-form-item>
          <n-form-item label="Chat ID">
            <n-input v-model:value="form.config.chat_ids" placeholder="接收通知的 Chat ID，多个用逗号分隔" />
          </n-form-item>
          <div style="font-size:12px;color:#999;padding:8px 12px;background:rgba(0,122,255,0.05);border-radius:8px;border-left:3px solid #007AFF;margin-bottom:8px;line-height:1.6">
            此处仅用于接收通知推送。如需交互式管理设备（开关机/查状态），请在「触发源」中添加 Telegram Bot 并开启「同步通知渠道」。
          </div>
        </template>
        <template v-else>
          <n-form-item label="模板">
            <n-radio-group :value="selectedPreset" @update:value="applyPreset" size="small">
              <n-radio-button v-for="(p, key) in webhookPresets" :key="key" :value="key">{{ p.label }}</n-radio-button>
            </n-radio-group>
          </n-form-item>
          <n-form-item label="URL"><n-input v-model:value="form.config.url" :placeholder="webhookPresets[selectedPreset]?.url_hint || 'https://...'" /></n-form-item>
          <n-form-item label="方法">
            <n-select v-model:value="form.config.method" :options="[{label:'POST',value:'POST'},{label:'GET',value:'GET'}]" style="width:120px" />
          </n-form-item>
          <n-form-item v-if="showHeaderEditor" label="请求头">
            <n-input v-model:value="form.config.headers" type="textarea" :rows="3" placeholder='{"Content-Type": "application/json"}' style="font-family:monospace;font-size:12px" />
          </n-form-item>
          <n-form-item label="请求体">
            <n-input v-model:value="form.config.body_template" type="textarea" :rows="6" placeholder='{"title": "{title}", "body": "{body}"}' style="font-family:monospace;font-size:12px" />
            <template #feedback>
              <span style="color:#999;font-size:12px">变量：<code>{title}</code> → 通知标题（如「WoL 开机成功」），<code>{body}</code> → 通知详情（如设备名称、IP、操作结果）</span>
            </template>
          </n-form-item>
        </template>
      </n-form>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <n-button @click="showForm = false">返回</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
      </div>
    </template>
  </n-modal>
</template>
