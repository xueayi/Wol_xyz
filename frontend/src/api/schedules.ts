import api from '.'

export const getSchedules = () => api.get('/schedules')
export const createSchedule = (data: any) => api.post('/schedules', data)
export const updateSchedule = (id: number, data: any) => api.put(`/schedules/${id}`, data)
export const deleteSchedule = (id: number) => api.delete(`/schedules/${id}`)
