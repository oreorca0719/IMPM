import axios from 'axios'

// JWT 를 자동 첨부하고, 401 시 로그인으로 유도하는 axios 인스턴스.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
})

export const TOKEN_KEY = 'impm_token'

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      // 로그인 페이지가 아니면 이동
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign('/login')
      }
    }
    return Promise.reject(err)
  },
)

export default client
