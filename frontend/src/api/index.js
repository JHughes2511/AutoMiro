import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const projects = {
  list: ()                           => api.get('/projects/'),
  create: (name, brief)              => api.post('/projects/', { name, brief }),
  get: (id)                          => api.get(`/projects/${id}`),
  clarify: (id)                      => api.get(`/projects/${id}/clarify`),
  submitClarifications: (id, data)   => api.post(`/projects/${id}/clarify`, { clarifications: data }),
  addToBrief: (id, input)            => api.post(`/projects/${id}/add`, { input }),
  start: (id)                        => api.post(`/projects/${id}/start`),
  chat: (id, domain, message)        => api.post(`/projects/${id}/chat/${domain}`, { message }),
}

export const agents = {
  status: (id) => api.get(`/agents/${id}/status`),
}

export const output = {
  report: (id)  => api.get(`/output/${id}/report`),
  vision: (id)  => api.get(`/output/${id}/vision`),
}
