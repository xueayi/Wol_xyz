<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { changePassword, changeUsername, regenerateSecret } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show'])
const msg = useMessage()
const auth = useAuthStore()

const activeTab = ref('password')
const pwdForm = ref({ current: '', newPwd: '', confirm: '' })
const usernameForm = ref({ newUsername: '', password: '' })
const saving = ref(false)

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
    </n-tabs>
  </n-modal>
</template>
