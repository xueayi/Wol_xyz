import api from '.'

export const getDevices = (groupId?: number) =>
  api.get('/devices', { params: groupId ? { group_id: groupId } : {} })

export const createDevice = (data: any) => api.post('/devices', data)
export const updateDevice = (id: number, data: any) => api.put(`/devices/${id}`, data)
export const deleteDevice = (id: number) => api.delete(`/devices/${id}`)
export const wakeDevice = (id: number) => api.post(`/devices/${id}/wake`)
export const shutdownDevice = (id: number) => api.post(`/devices/${id}/shutdown`)
export const generateKeypair = () => api.post('/devices/generate-keypair')
export const batchDeleteDevices = (ids: number[]) => api.post('/devices/batch-delete', { ids })
export const batchMoveDevices = (ids: number[], group_id: number | null) => api.post('/devices/batch-move', { ids, group_id })
