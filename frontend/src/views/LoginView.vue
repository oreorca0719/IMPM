<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.replace(route.query.redirect || '/board')
  } catch (e) {
    error.value =
      e.response?.data?.detail || '로그인에 실패했습니다. 다시 시도해 주세요.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="min-h-screen flex items-center justify-center bg-slate-100">
    <form
      class="w-full max-w-sm bg-white rounded-2xl shadow-lg p-8 space-y-5"
      @submit.prevent="submit"
    >
      <div class="text-center space-y-1">
        <h1 class="text-2xl font-bold text-brand-600">IMPM</h1>
        <p class="text-sm text-slate-500">STRIPE 프로젝트 관리</p>
      </div>

      <div class="space-y-1">
        <label class="text-sm font-medium text-slate-700">이메일</label>
        <input
          v-model="email"
          type="email"
          required
          autocomplete="username"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
        />
      </div>

      <div class="space-y-1">
        <label class="text-sm font-medium text-slate-700">비밀번호</label>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
        />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-lg bg-brand-600 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {{ loading ? '로그인 중…' : '로그인' }}
      </button>
    </form>
  </main>
</template>
