import api from '.'

export const getTriggers = () => api.get('/triggers')
export const getTriggerStatus = () => api.get('/triggers/status')
export const createTrigger = (data: any) => api.post('/triggers', data)
export const updateTrigger = (id: number, data: any) => api.put(`/triggers/${id}`, data)
export const deleteTrigger = (id: number) => api.delete(`/triggers/${id}`)
