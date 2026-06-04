import api from '.'

export const login = (username: string, password: string) =>
  api.post('/auth/login', { username, password })

export const getMe = () => api.get('/auth/me')

export const changePassword = (current_password: string, new_password: string) =>
  api.put('/auth/password', { current_password, new_password })

export const changeUsername = (new_username: string, password: string) =>
  api.put('/auth/username', { new_username, password })

export const regenerateSecret = () =>
  api.post('/auth/regenerate-secret')
