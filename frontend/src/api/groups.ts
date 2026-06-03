import api from '.'

export const getGroups = () => api.get('/groups')
export const getGroupsWithDevices = () => api.get('/groups/with-devices')
export const createGroup = (data: any) => api.post('/groups', data)
export const updateGroup = (id: number, data: any) => api.put(`/groups/${id}`, data)
export const deleteGroup = (id: number) => api.delete(`/groups/${id}`)
