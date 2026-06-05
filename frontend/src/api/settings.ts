import api from '.'

export const getProxyConfig = () => api.get('/settings/proxy')
export const updateProxyConfig = (data: any) => api.put('/settings/proxy', data)
export const testProxyConfig = (data: any) => api.post('/settings/proxy/test', data)
