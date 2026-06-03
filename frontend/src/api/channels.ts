import api from '.'

export const getChannels = () => api.get('/channels')
export const createChannel = (data: any) => api.post('/channels', data)
export const updateChannel = (id: number, data: any) => api.put(`/channels/${id}`, data)
export const deleteChannel = (id: number) => api.delete(`/channels/${id}`)
export const testChannel = (id: number) => api.post(`/channels/${id}/test`)
