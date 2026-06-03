import api from '.'

export const getDashboardStats = () => api.get('/dashboard/stats')
export const getLogs = (params?: any) => api.get('/logs', { params })
export const scanLan = () => api.post('/scan/start')
