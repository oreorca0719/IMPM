<script setup>
import { ref } from 'vue'
import { authApi } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

// 프로필(아이디·이름)
const email = ref(auth.user?.email || '')
const name = ref(auth.user?.name || '')
const profilePassword = ref('')
const profileMsg = ref('')
const profileErr = ref('')
const savingProfile = ref(false)

// 비밀번호
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const pwMsg = ref('')
const pwErr = ref('')
const savingPw = ref(false)

async function saveProfile() {
  profileMsg.value = ''
  profileErr.value = ''
  if (!profilePassword.value) return (profileErr.value = '현재 비밀번호를 입력해 주세요.')
  savingProfile.value = true
  try {
    const { data } = await authApi.updateMe({
      email: email.value,
      name: name.value,
      current_password: profilePassword.value,
    })
    auth.setUser(data)
    profilePassword.value = ''
    profileMsg.value = '저장되었습니다.'
  } catch (e) {
    profileErr.value = e.response?.data?.detail || '저장에 실패했습니다.'
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  pwMsg.value = ''
  pwErr.value = ''
  if (newPassword.value.length < 8) return (pwErr.value = '새 비밀번호는 8자 이상이어야 합니다.')
  if (newPassword.value !== confirmPassword.value)
    return (pwErr.value = '새 비밀번호가 서로 일치하지 않습니다.')
  savingPw.value = true
  try {
    const { data } = await authApi.changePassword(currentPassword.value, newPassword.value)
    auth.setUser(data)
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    pwMsg.value = '비밀번호가 변경되었습니다.'
  } catch (e) {
    pwErr.value = e.response?.data?.detail || '변경에 실패했습니다.'
  } finally {
    savingPw.value = false
  }
}
</script>

<template>
  <div class="px-8 py-6 max-w-xl space-y-5">
    <header>
      <h1 class="text-xl font-semibold text-slate-900">계정 설정</h1>
      <p class="text-sm text-slate-400 mt-0.5">아이디·이름·비밀번호를 변경합니다</p>
    </header>

    <!-- 프로필 -->
    <section class="card p-5 space-y-4">
      <h2 class="text-sm font-semibold text-slate-700">아이디 · 이름</h2>
      <div>
        <label class="field-label">아이디 (이메일)</label>
        <input v-model="email" type="email" class="input" />
      </div>
      <div>
        <label class="field-label">이름</label>
        <input v-model="name" type="text" class="input" />
      </div>
      <div>
        <label class="field-label">현재 비밀번호 (본인 확인)</label>
        <input v-model="profilePassword" type="password" autocomplete="current-password" class="input" />
      </div>
      <p v-if="profileErr" class="text-sm text-red-600">{{ profileErr }}</p>
      <p v-if="profileMsg" class="text-sm text-green-600">{{ profileMsg }}</p>
      <div class="flex justify-end">
        <button :disabled="savingProfile" class="btn btn-primary btn-md" @click="saveProfile">
          {{ savingProfile ? '저장 중…' : '저장' }}
        </button>
      </div>
    </section>

    <!-- 비밀번호 -->
    <section class="card p-5 space-y-4">
      <h2 class="text-sm font-semibold text-slate-700">비밀번호 변경</h2>
      <div>
        <label class="field-label">현재 비밀번호</label>
        <input v-model="currentPassword" type="password" autocomplete="current-password" class="input" />
      </div>
      <div>
        <label class="field-label">새 비밀번호 (8자 이상)</label>
        <input v-model="newPassword" type="password" autocomplete="new-password" class="input" />
      </div>
      <div>
        <label class="field-label">새 비밀번호 확인</label>
        <input v-model="confirmPassword" type="password" autocomplete="new-password" class="input" />
      </div>
      <p v-if="pwErr" class="text-sm text-red-600">{{ pwErr }}</p>
      <p v-if="pwMsg" class="text-sm text-green-600">{{ pwMsg }}</p>
      <div class="flex justify-end">
        <button :disabled="savingPw" class="btn btn-primary btn-md" @click="savePassword">
          {{ savingPw ? '변경 중…' : '비밀번호 변경' }}
        </button>
      </div>
    </section>
  </div>
</template>
