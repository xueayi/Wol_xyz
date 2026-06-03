<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { getTriggers, createTrigger, updateTrigger, deleteTrigger } from '../../api/triggers'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show', 'saved'])
const msg = useMessage()

const triggers = ref<any[]>([])
const showForm = ref(false)
const editItem = ref<any>(null)
const form = ref({ type: 'http_api', name: '', config: {} as any, enabled: true })
const saving = ref(false)

const typeOptions = [
  { label: 'HTTP API', value: 'http_api' },
  { label: '巴法云 (Bemfa)', value: 'bemfa' },
  { label: 'MQTT', value: 'mqtt' },
  { label: 'Telegram Bot', value: 'telegram' },
]

const typeLabel: Record<string, string> = {
  http_api: 'HTTP API',
  bemfa: '巴法云',
  mqtt: 'MQTT',
  telegram: 'Telegram',
}

async function loadData() {
  const { data } = await getTriggers()
  triggers.value = data
}

function getDefaults(type: string): any {
  switch (type) {
    case 'http_api': return { token: '' }
    case 'bemfa': return { uid: '', topic: '' }
    case 'mqtt': return { broker: '', port: 1883, username: '', password: '', topic: 'xiaoxue_wol/#' }
    case 'telegram': return { bot_token: '', allowed_chat_ids: '' }
    default: return {}
  }
}

function openAdd() {
  editItem.value = null
  form.value = { type: 'http_api', name: '', config: getDefaults('http_api'), enabled: true }
  showForm.value = true
}

function openEdit(item: any) {
  editItem.value = item
  form.value = { type: item.type, name: item.name, config: { ...item.config }, enabled: item.enabled }
  showForm.value = true
}

function onTypeChange(val: string) {
  form.value.type = val
  form.value.config = getDefaults(val)
}

async function handleSave() {
  if (!form.value.name.trim()) { msg.warning('请输入名称'); return }
  saving.value = true
  try {
    if (editItem.value) await updateTrigger(editItem.value.id, form.value)
    else await createTrigger(form.value)
    showForm.value = false
    await loadData()
    emit('saved')
  } catch (e: any) { msg.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function handleDelete(id: number) {
  await deleteTrigger(id)
  await loadData()
  emit('saved')
}

function generateToken() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 32; i++) result += chars.charAt(Math.floor(Math.random() * chars.length))
  form.value.config.token = result
}
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="触发源管理" style="width: 640px" :bordered="false" @after-enter="loadData">
    <template v-if="!showForm">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <n-button size="small" tertiary @click="openAdd">+ 新建触发源</n-button>
      </div>
      <div v-if="triggers.length === 0" style="text-align:center;color:#999;padding:24px 0;font-size:13px">
        暂无触发源，点击上方按钮添加
      </div>
      <n-table v-else :bordered="false" :single-line="false" size="small">
        <thead><tr><th>名称</th><th>类型</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="t in triggers" :key="t.id">
            <td>{{ t.name }}</td>
            <td>{{ typeLabel[t.type] || t.type }}</td>
            <td><n-tag :type="t.enabled ? 'success' : 'default'" size="tiny">{{ t.enabled ? '启用' : '禁用' }}</n-tag></td>
            <td style="display:flex;gap:4px">
              <n-button text size="tiny" @click="openEdit(t)">编辑</n-button>
              <n-popconfirm @positive-click="handleDelete(t.id)">
                <template #trigger><n-button text size="tiny" type="error">删除</n-button></template>
                确定删除此触发源？
              </n-popconfirm>
            </td>
          </tr>
        </tbody>
      </n-table>
    </template>
    <template v-else>
      <n-form label-placement="left" label-width="90">
        <n-form-item label="类型">
          <n-select :value="form.type" @update:value="onTypeChange" :options="typeOptions" :disabled="!!editItem" style="width:200px" />
        </n-form-item>
        <n-form-item label="名称"><n-input v-model:value="form.name" placeholder="为该触发源命名" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>

        <n-divider>{{ typeLabel[form.type] }} 配置</n-divider>

        <template v-if="form.type === 'http_api'">
          <n-form-item label="Token">
            <n-input-group>
              <n-input v-model:value="form.config.token" placeholder="访问令牌" style="font-family:monospace" />
              <n-button @click="generateToken" style="flex-shrink:0">随机生成</n-button>
            </n-input-group>
          </n-form-item>
          <div class="config-hint">
            调用方式：<code>GET /api/external/trigger?token=TOKEN&amp;mac=MAC&amp;action=wake</code>
          </div>
        </template>

        <template v-if="form.type === 'bemfa'">
          <n-form-item label="UID (私钥)"><n-input v-model:value="form.config.uid" placeholder="巴法云控制台获取" /></n-form-item>
          <n-form-item label="Topic"><n-input v-model:value="form.config.topic" placeholder="巴法云主题名称" /></n-form-item>
          <div class="config-hint">
            在 <a href="https://cloud.bemfa.com" target="_blank" style="color:#007AFF">cloud.bemfa.com</a> 注册获取 UID，创建「插座」类型 Topic
          </div>
        </template>

        <template v-if="form.type === 'mqtt'">
          <n-form-item label="Broker"><n-input v-model:value="form.config.broker" placeholder="MQTT Broker 地址" /></n-form-item>
          <n-form-item label="端口"><n-input-number v-model:value="form.config.port" :min="1" :max="65535" style="width:140px" /></n-form-item>
          <n-form-item label="用户名"><n-input v-model:value="form.config.username" placeholder="可选" /></n-form-item>
          <n-form-item label="密码"><n-input v-model:value="form.config.password" type="password" show-password-on="click" placeholder="可选" /></n-form-item>
          <n-form-item label="Topic"><n-input v-model:value="form.config.topic" placeholder="xiaoxue_wol/#" /></n-form-item>
          <div class="config-hint">
            向 Topic 发送 <code>on</code> 开机 / <code>off</code> 关机
          </div>
        </template>

        <template v-if="form.type === 'telegram'">
          <n-form-item label="Bot Token"><n-input v-model:value="form.config.bot_token" placeholder="从 @BotFather 获取" style="font-family:monospace" /></n-form-item>
          <n-form-item label="允许的 Chat ID">
            <n-input v-model:value="form.config.allowed_chat_ids" placeholder="多个用逗号分隔，留空则不限制" />
          </n-form-item>
          <div class="config-hint">
            在 Telegram 中搜索 <a href="https://t.me/BotFather" target="_blank" style="color:#007AFF">@BotFather</a> 创建 Bot 获取 Token。Chat ID 可通过 <a href="https://t.me/userinfobot" target="_blank" style="color:#007AFF">@userinfobot</a> 获取。Bot 支持命令：/devices 查看设备、点击按钮开关机、/scan 扫描局域网、/logs 查看日志。
          </div>
        </template>
      </n-form>
      <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
        <n-button @click="showForm = false">返回</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.config-hint {
  font-size: 12px;
  color: #999;
  padding: 8px 12px;
  background: rgba(0, 122, 255, 0.05);
  border-radius: 8px;
  border-left: 3px solid #007AFF;
  margin-bottom: 8px;
  line-height: 1.6;
}
.config-hint code {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'SF Mono', SFMono-Regular, Menlo, monospace;
}
</style>
