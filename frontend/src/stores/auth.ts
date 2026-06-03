import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, getMe } from '../api/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const token = ref(localStorage.getItem('xwol_token') || '')

  async function login(username: string, password: string) {
    const { data } = await apiLogin(username, password)
    token.value = data.access_token
    localStorage.setItem('xwol_token', data.access_token)
    await fetchUser()
    router.push('/')
  }

  async function fetchUser() {
    try {
      const { data } = await getMe()
      user.value = data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('xwol_token')
    router.push('/login')
  }

  return { user, token, login, fetchUser, logout }
})
