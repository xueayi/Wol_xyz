<script setup lang="ts">
import { ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { changePassword, changeUsername, regenerateSecret } from '../../api/auth'
import { getProxyConfig, updateProxyConfig, testProxyConfig } from '../../api/settings'
import { useAuthStore } from '../../stores/auth'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show'])
const msg = useMessage()
const auth = useAuthStore()

const activeTab = ref('password')
const pwdForm = ref({ current: '', newPwd: '', confirm: '' })
const usernameForm = ref({ newUsername: '', password: '' })
const saving = ref(false)

const proxyForm = ref({
  proxy_enabled: false,
  proxy_type: 'http',
  proxy_host: '',
  proxy_port: 7890,
  proxy_username: '',
  proxy_password: '',
})
const proxyLoading = ref(false)
const proxyTesting = ref(false)

watch(() => props.show, async (val) => {
  if (val && activeTab.value === 'proxy') {
    await loadProxy()
  }
})

watch(activeTab, async (val) => {
  if (val === 'proxy') await loadProxy()
})

async function loadProxy() {
  proxyLoading.value = true
  try {
    const { data } = await getProxyConfig()
    proxyForm.value = data
  } catch { /* ignore */ }
  finally { proxyLoading.value = false }
}

async function handleSaveProxy() {
  saving.value = true
  try {
    await updateProxyConfig(proxyForm.value)
    msg.success('代理配置已保存，立即生效')
  } catch (e: any) {
    msg.error(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

async function handleTestProxy() {
  proxyTesting.value = true
  try {
    const { data } = await testProxyConfig(proxyForm.value)
    data.success ? msg.success(data.detail) : msg.error(data.detail)
  } catch (e: any) {
    msg.error('测试失败')
  } finally { proxyTesting.value = false }
}

async function handleChangePassword() {
  if (!pwdForm.value.current || !pwdForm.value.newPwd) {
    msg.warning('请填写完整'); return
  }
  if (pwdForm.value.newPwd !== pwdForm.value.confirm) {
    msg.warning('两次输入的新密码不一致'); return
  }
  saving.value = true
  try {
    await changePassword(pwdForm.value.current, pwdForm.value.newPwd)
    msg.success('密码修改成功，请重新登录')
    auth.logout()
  } catch (e: any) {
    msg.error(e.response?.data?.detail || '修改失败')
  } finally { saving.value = false }
}

async function handleChangeUsername() {
  if (!usernameForm.value.newUsername || !usernameForm.value.password) {
    msg.warning('请填写完整'); return
  }
  saving.value = true
  try {
    const { data } = await changeUsername(usernameForm.value.newUsername, usernameForm.value.password)
    localStorage.setItem('xwol_token', data.access_token)
    msg.success('用户名修改成功')
    await auth.fetchUser()
    emit('update:show', false)
  } catch (e: any) {
    msg.error(e.response?.data?.detail || '修改失败')
  } finally { saving.value = false }
}

async function handleRegenSecret() {
  saving.value = true
  try {
    await regenerateSecret()
    msg.success('密钥已重新生成，重启服务后生效')
  } catch (e: any) {
    msg.error(e.response?.data?.detail || '操作失败')
  } finally { saving.value = false }
}
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="用户管理" style="width: 480px" :bordered="false">
    <n-tabs v-model:value="activeTab" type="segment" animated>
      <n-tab-pane name="password" tab="修改密码">
        <n-form label-placement="top" style="margin-top: 8px">
          <n-form-item label="当前密码">
            <n-input v-model:value="pwdForm.current" type="password" show-password-on="click" placeholder="请输入当前密码" />
          </n-form-item>
          <n-form-item label="新密码">
            <n-input v-model:value="pwdForm.newPwd" type="password" show-password-on="click" placeholder="请输入新密码" />
          </n-form-item>
          <n-form-item label="确认新密码">
            <n-input v-model:value="pwdForm.confirm" type="password" show-password-on="click" placeholder="再次输入新密码" />
          </n-form-item>
          <n-button type="primary" block :loading="saving" @click="handleChangePassword">修改密码</n-button>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="username" tab="修改用户名">
        <n-form label-placement="top" style="margin-top: 8px">
          <n-form-item label="新用户名">
            <n-input v-model:value="usernameForm.newUsername" placeholder="请输入新用户名" />
          </n-form-item>
          <n-form-item label="验证密码">
            <n-input v-model:value="usernameForm.password" type="password" show-password-on="click" placeholder="请输入当前密码验证身份" />
          </n-form-item>
          <n-button type="primary" block :loading="saving" @click="handleChangeUsername">修改用户名</n-button>
        </n-form>
      </n-tab-pane>

      <n-tab-pane name="secret" tab="安全密钥">
        <div style="padding: 12px 0; color: #666; font-size: 14px; line-height: 1.8">
          <p>JWT 签名密钥用于认证令牌的加密。重新生成后需要重启服务，所有已登录用户将需要重新登录。</p>
          <n-button type="warning" block :loading="saving" @click="handleRegenSecret" style="margin-top: 12px">
            重新生成密钥
          </n-button>
        </div>
      </n-tab-pane>

      <n-tab-pane name="proxy" tab="代理设置">
        <n-spin :show="proxyLoading">
          <n-form label-placement="left" label-width="80" style="margin-top: 8px">
            <n-form-item label="启用代理">
              <n-switch v-model:value="proxyForm.proxy_enabled" />
              <span style="margin-left:8px;font-size:12px;color:#999">{{ proxyForm.proxy_enabled ? '已启用，保存后立即生效' : '关闭后代理不会应用于请求' }}</span>
            </n-form-item>
            <n-form-item label="代理类型">
              <n-radio-group v-model:value="proxyForm.proxy_type">
                <n-radio-button value="http">HTTP</n-radio-button>
                <n-radio-button value="socks5">SOCKS5</n-radio-button>
              </n-radio-group>
            </n-form-item>
            <n-form-item label="地址">
              <n-input v-model:value="proxyForm.proxy_host" placeholder="127.0.0.1" />
            </n-form-item>
            <n-form-item label="端口">
              <n-input-number v-model:value="proxyForm.proxy_port" :min="1" :max="65535" style="width: 140px" />
            </n-form-item>
            <n-form-item label="用户名">
              <n-input v-model:value="proxyForm.proxy_username" placeholder="可选" />
            </n-form-item>
            <n-form-item label="密码">
              <n-input v-model:value="proxyForm.proxy_password" type="password" show-password-on="click" placeholder="可选" />
            </n-form-item>
            <div style="display:flex;gap:8px">
              <n-button type="primary" :loading="saving" @click="handleSaveProxy" style="flex:1">保存</n-button>
              <n-button :loading="proxyTesting" @click="handleTestProxy" :disabled="!proxyForm.proxy_host">测试连接</n-button>
            </div>
            <div style="font-size:12px;color:#999;margin-top:12px;line-height:1.6;padding:8px 12px;background:rgba(0,122,255,0.05);border-radius:8px;border-left:3px solid #007AFF">
              代理用于 Telegram Bot、Webhook 通知等需要访问外网的服务。保存后立即生效，无需重启。
            </div>
          </n-form>
        </n-spin>
      </n-tab-pane>
    </n-tabs>
  </n-modal>
</template>
