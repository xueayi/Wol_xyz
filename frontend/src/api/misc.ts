import api from '.'

export const getDashboardStats = () => api.get('/dashboard/stats')
export const getLogs = (params?: any) => api.get('/logs', { params })
export const scanLan = () => api.post('/scan/start')

export const getAnnouncements = () => api.get('/announcements')
export const createAnnouncement = (data: any) => api.post('/announcements', data)
export const updateAnnouncement = (id: number, data: any) => api.put(`/announcements/${id}`, data)
export const deleteAnnouncement = (id: number) => api.delete(`/announcements/${id}`)
