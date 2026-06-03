import axios from 'axios'
import router from '../router'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('xwol_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('xwol_token')
      router.push('/login')
    }
    return Promise.reject(err)
  },
)

export default api
