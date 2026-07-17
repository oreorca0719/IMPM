// API 호출 모음 — 화면/스토어에서 이걸 통해 백엔드에 접근.
import client from './client'

export const authApi = {
  login: (email, password) => client.post('/auth/login', { email, password }),
  me: () => client.get('/auth/me'),
}

export const userApi = {
  list: () => client.get('/users'),
}

export const projectApi = {
  list: () => client.get('/projects'),
  get: (pid) => client.get(`/projects/${pid}`),
  create: (data) => client.post('/projects', data),
}

export const epicApi = {
  list: (pid) => client.get(`/projects/${pid}/epics`),
  create: (pid, data) => client.post(`/projects/${pid}/epics`, data),
  update: (id, data) => client.patch(`/epics/${id}`, data),
  remove: (id) => client.delete(`/epics/${id}`),
}

export const issueApi = {
  list: (pid, params) => client.get(`/projects/${pid}/issues`, { params }),
  create: (pid, data) => client.post(`/projects/${pid}/issues`, data),
  get: (id) => client.get(`/issues/${id}`),
  update: (id, data) => client.patch(`/issues/${id}`, data),
  remove: (id) => client.delete(`/issues/${id}`),
  move: (id, status, board_order) =>
    client.patch(`/issues/${id}/move`, { status, board_order }),
  addLabel: (id, label_id) => client.post(`/issues/${id}/labels`, { label_id }),
  removeLabel: (id, label_id) => client.delete(`/issues/${id}/labels/${label_id}`),
}

export const labelApi = {
  list: (pid) => client.get(`/projects/${pid}/labels`),
  create: (pid, data) => client.post(`/projects/${pid}/labels`, data),
}

export const commentApi = {
  list: (issueId) => client.get(`/issues/${issueId}/comments`),
  create: (issueId, body) => client.post(`/issues/${issueId}/comments`, { body }),
  update: (cid, body) => client.patch(`/comments/${cid}`, { body }),
  remove: (cid) => client.delete(`/comments/${cid}`),
  activity: (issueId) => client.get(`/issues/${issueId}/activity`),
}

export const dashboardApi = {
  get: (pid) => client.get(`/projects/${pid}/dashboard`),
}
