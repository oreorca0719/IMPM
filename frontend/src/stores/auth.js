import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '../api'
import { TOKEN_KEY } from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')

  async function login(email, password) {
    const { data } = await authApi.login(email, password)
    token.value = data.access_token
    localStorage.setItem(TOKEN_KEY, data.access_token)
    user.value = data.user
    return data.user
  }

  async function fetchMe() {
    const { data } = await authApi.me()
    user.value = data
    return data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  const isAuthed = () => !!token.value

  return { user, token, login, fetchMe, logout, isAuthed }
})
