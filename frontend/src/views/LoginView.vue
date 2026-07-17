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
  <main class="min-h-screen flex items-center justify-center bg-slate-50 px-4">
    <div class="w-full max-w-sm">
      <!-- 로고 -->
      <div class="flex flex-col items-center mb-8">
        <div class="h-12 w-12 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm mb-3">
          <span class="text-white font-bold text-lg tracking-tight">IM</span>
        </div>
        <h1 class="text-lg font-semibold text-slate-900">IMPM</h1>
        <p class="text-sm text-slate-500 mt-0.5">STRIPE 프로젝트 관리</p>
      </div>

      <form class="card soft-shadow p-7 space-y-4" @submit.prevent="submit">
        <div>
          <label class="field-label">이메일</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="username"
            placeholder="you@impm.team"
            class="input"
          />
        </div>

        <div>
          <label class="field-label">비밀번호</label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            placeholder="••••••••"
            class="input"
          />
        </div>

        <p v-if="error" class="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
          {{ error }}
        </p>

        <button type="submit" :disabled="loading" class="btn btn-primary btn-md w-full">
          {{ loading ? '로그인 중…' : '로그인' }}
        </button>
      </form>

      <p class="text-center text-xs text-slate-400 mt-6">
        경기청년 갭이어 · STRIPE 개발 프로젝트 관리
      </p>
    </div>
  </main>
</template>
