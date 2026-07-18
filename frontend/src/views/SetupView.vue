<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref(auth.user?.email || '')
const name = ref(auth.user?.name || '')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const saving = ref(false)

const pwTooShort = computed(() => newPassword.value.length > 0 && newPassword.value.length < 8)
const pwMismatch = computed(
  () => confirmPassword.value.length > 0 && newPassword.value !== confirmPassword.value,
)

async function submit() {
  error.value = ''
  if (!currentPassword.value) return (error.value = '현재(임시) 비밀번호를 입력해 주세요.')
  if (newPassword.value.length < 8) return (error.value = '새 비밀번호는 8자 이상이어야 합니다.')
  if (newPassword.value !== confirmPassword.value)
    return (error.value = '새 비밀번호가 서로 일치하지 않습니다.')
  if (newPassword.value === currentPassword.value)
    return (error.value = '새 비밀번호가 현재 비밀번호와 같습니다.')

  saving.value = true
  try {
    // 1) 아이디(이메일)·이름이 바뀌었으면 먼저 반영
    const emailChanged = email.value && email.value !== auth.user?.email
    const nameChanged = name.value && name.value !== auth.user?.name
    if (emailChanged || nameChanged) {
      const { data } = await authApi.updateMe({
        email: email.value,
        name: name.value,
        current_password: currentPassword.value,
      })
      auth.setUser(data)
    }
    // 2) 비밀번호 변경(성공 시 '변경 필요' 플래그 해제)
    const { data } = await authApi.changePassword(currentPassword.value, newPassword.value)
    auth.setUser(data)
    router.replace('/board')
  } catch (e) {
    error.value = e.response?.data?.detail || '변경에 실패했습니다. 다시 시도해 주세요.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <main class="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-10">
    <div class="w-full max-w-md">
      <div class="flex flex-col items-center mb-7">
        <div class="h-12 w-12 rounded-xl bg-indigo-600 flex items-center justify-center shadow-sm mb-3">
          <span class="text-white font-bold text-lg">IM</span>
        </div>
        <h1 class="text-lg font-semibold text-slate-900">초기 설정</h1>
        <p class="text-sm text-slate-500 mt-1 text-center">
          보안을 위해 처음 로그인 시<br />아이디와 비밀번호를 변경해 주세요.
        </p>
      </div>

      <form class="card soft-shadow p-7 space-y-4" @submit.prevent="submit">
        <div>
          <label class="field-label">아이디 (이메일)</label>
          <input v-model="email" type="email" required class="input" />
          <p class="text-xs text-slate-400 mt-1">앞으로 이 주소로 로그인합니다.</p>
        </div>

        <div>
          <label class="field-label">이름</label>
          <input v-model="name" type="text" required class="input" />
        </div>

        <hr class="border-slate-100" />

        <div>
          <label class="field-label">현재(임시) 비밀번호</label>
          <input v-model="currentPassword" type="password" required autocomplete="current-password" class="input" />
        </div>

        <div>
          <label class="field-label">새 비밀번호</label>
          <input v-model="newPassword" type="password" required autocomplete="new-password" class="input" />
          <p class="text-xs mt-1" :class="pwTooShort ? 'text-red-500' : 'text-slate-400'">
            8자 이상으로 입력해 주세요.
          </p>
        </div>

        <div>
          <label class="field-label">새 비밀번호 확인</label>
          <input v-model="confirmPassword" type="password" required autocomplete="new-password" class="input" />
          <p v-if="pwMismatch" class="text-xs text-red-500 mt-1">비밀번호가 일치하지 않습니다.</p>
        </div>

        <p v-if="error" class="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{{ error }}</p>

        <button type="submit" :disabled="saving" class="btn btn-primary btn-md w-full">
          {{ saving ? '저장 중…' : '저장하고 시작하기' }}
        </button>
      </form>
    </div>
  </main>
</template>
