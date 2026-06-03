<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const msg = useMessage()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    msg.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(username.value, password.value)
  } catch {
    msg.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg-orb orb-1" />
    <div class="login-bg-orb orb-2" />
    <div class="login-bg-orb orb-3" />

    <div class="login-card">
      <div class="login-header">
        <div class="app-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#g1)"/>
            <path d="M14 28V20a10 10 0 0120 0v8" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="24" cy="32" r="3" fill="#fff"/>
            <defs><linearGradient id="g1" x1="0" y1="0" x2="48" y2="48"><stop stop-color="#007AFF"/><stop offset="1" stop-color="#5856D6"/></linearGradient></defs>
          </svg>
        </div>
        <h1>XiaoXue WoL</h1>
        <p>局域网设备管理</p>
      </div>

      <n-form @submit.prevent="handleLogin">
        <n-form-item label="用户名" :show-feedback="false" style="margin-bottom: 16px">
          <n-input v-model:value="username" placeholder="请输入用户名" size="large" round />
        </n-form-item>
        <n-form-item label="密码" :show-feedback="false" style="margin-bottom: 24px">
          <n-input v-model:value="password" type="password" placeholder="请输入密码" size="large" round
            show-password-on="click" @keyup.enter="handleLogin" />
        </n-form-item>
        <n-button type="primary" block size="large" round :loading="loading" @click="handleLogin">
          登 录
        </n-button>
      </n-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  position: relative;
  overflow: hidden;
}

.login-bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
}
.orb-1 {
  width: 400px; height: 400px;
  background: #007AFF;
  top: -100px; left: -100px;
  animation: float 8s ease-in-out infinite;
}
.orb-2 {
  width: 350px; height: 350px;
  background: #5856D6;
  bottom: -80px; right: -80px;
  animation: float 10s ease-in-out infinite reverse;
}
.orb-3 {
  width: 250px; height: 250px;
  background: #34C759;
  top: 50%; left: 60%;
  animation: float 12s ease-in-out infinite 2s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.login-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(40px) saturate(150%);
  -webkit-backdrop-filter: blur(40px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 44px 36px 36px;
  width: 380px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
  color: #fff;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}
.app-icon {
  margin-bottom: 16px;
}
.login-header h1 {
  margin: 0 0 4px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}
.login-header p {
  margin: 0;
  color: rgba(255,255,255,0.6);
  font-size: 14px;
  font-weight: 400;
}

.login-card :deep(.n-form-item-label) {
  color: rgba(255,255,255,0.7) !important;
  font-size: 13px;
  font-weight: 500;
}
.login-card :deep(.n-input) {
  --n-border: 1px solid rgba(255,255,255,0.15) !important;
  --n-color: rgba(255,255,255,0.08) !important;
  --n-color-focus: rgba(255,255,255,0.12) !important;
  --n-text-color: #fff !important;
  --n-placeholder-color: rgba(255,255,255,0.35) !important;
  --n-caret-color: #007AFF !important;
  --n-border-focus: 1px solid rgba(0,122,255,0.6) !important;
  --n-box-shadow-focus: 0 0 0 2px rgba(0,122,255,0.2) !important;
}
.login-card :deep(.n-button--primary-type) {
  --n-color: #007AFF !important;
  --n-color-hover: #0A84FF !important;
  --n-text-color: #fff !important;
  font-weight: 600;
  font-size: 16px;
  height: 46px !important;
}
</style>
