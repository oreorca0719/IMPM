<script setup>
import { onMounted, ref } from 'vue'
import { authApi } from '../api'
import { useAuthStore } from '../stores/auth'
import Icon from '../components/Icon.vue'

const auth = useAuthStore()

// Claude(MCP) 연동 토큰
const mcp = ref(null)
const showToken = ref(false)
const copied = ref('')
const rotating = ref(false)

onMounted(async () => {
  try {
    mcp.value = (await authApi.mcpToken()).data
  } catch {
    /* 조회 실패 시 섹션만 숨김 */
  }
})

function masked(t) {
  if (!t) return ''
  return t.slice(0, 6) + '•'.repeat(Math.max(0, t.length - 10)) + t.slice(-4)
}

async function copy(text, what) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = what
    setTimeout(() => (copied.value = ''), 1800)
  } catch {
    copied.value = ''
  }
}

async function rotate() {
  if (!confirm('토큰을 새로 발급하면 기존 토큰은 즉시 사용할 수 없습니다. 계속할까요?')) return
  rotating.value = true
  try {
    mcp.value = (await authApi.rotateMcpToken()).data
    showToken.value = true
  } finally {
    rotating.value = false
  }
}

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

    <!-- Claude(MCP) 연동 -->
    <section v-if="mcp" class="card p-5 space-y-4">
      <div>
        <h2 class="text-sm font-semibold text-slate-700">Claude 연동 (MCP)</h2>
        <p class="text-xs text-slate-400 mt-1">
          이 토큰으로 Claude를 연결하면, Claude로 한 작업이 <b>본인 이름</b>으로 기록됩니다.
        </p>
      </div>

      <!-- 토큰 -->
      <div>
        <label class="field-label">내 토큰</label>
        <div class="flex items-center gap-2">
          <code class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-mono text-slate-700 break-all">
            {{ showToken ? mcp.token : masked(mcp.token) }}
          </code>
          <button class="btn btn-secondary btn-sm shrink-0" @click="showToken = !showToken">
            {{ showToken ? '숨기기' : '보기' }}
          </button>
          <button class="btn btn-secondary btn-sm shrink-0" @click="copy(mcp.token, 'token')">
            {{ copied === 'token' ? '복사됨' : '복사' }}
          </button>
        </div>
        <p class="text-xs text-amber-600 mt-1.5">
          ⚠ 본인만 사용하세요. 다른 사람과 공유하면 그 사람의 작업이 내 이름으로 기록됩니다.
        </p>
      </div>

      <!-- ① 데스크톱 채팅 앱 -->
      <div class="rounded-lg bg-slate-50 border border-slate-200 p-4">
        <div class="text-sm font-medium text-slate-700 mb-1">① Claude 데스크톱 앱 (채팅)</div>
        <p class="text-xs text-slate-500 mb-2">
          설정 → 커넥터 → <b>커스텀 커넥터 추가</b>에서, 이름은 <code class="text-slate-700">IMPM</code>,
          <b>원격 MCP 서버 URL</b> 칸에 아래 주소를 붙여넣으세요. (OAuth 칸은 비워둡니다.)
        </p>
        <div class="flex items-center gap-2">
          <code class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-mono text-slate-700 break-all">{{ mcp.chat_url }}</code>
          <button class="btn btn-primary btn-sm shrink-0" @click="copy(mcp.chat_url, 'chat')">
            {{ copied === 'chat' ? '복사됨' : 'URL 복사' }}
          </button>
        </div>
        <p class="text-xs text-amber-600 mt-1.5">
          ⚠ 이 주소에는 토큰이 들어 있어 <b>비밀번호와 같습니다.</b> 공유·캡처에 주의하세요.
        </p>
      </div>

      <!-- ② Claude Code (CLI) -->
      <div>
        <label class="field-label">② Claude Code (터미널) — PowerShell 에 붙여넣기</label>
        <div class="rounded-lg border border-slate-200 bg-slate-900 p-3">
          <code class="block text-[11px] font-mono text-slate-100 whitespace-pre-wrap break-all">{{ mcp.connect_command }}</code>
        </div>
        <div class="flex items-center gap-2 mt-2">
          <button class="btn btn-secondary btn-sm" @click="copy(mcp.connect_command, 'cmd')">
            <Icon name="check" :size="14" v-if="copied === 'cmd'" />
            {{ copied === 'cmd' ? '복사됨' : '명령어 복사' }}
          </button>
        </div>
      </div>

      <!-- 재발급 -->
      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <p class="text-xs text-slate-500">
          토큰이 유출된 것 같으면 새로 발급하세요. (기존 토큰 즉시 무효)
        </p>
        <button :disabled="rotating" class="btn btn-secondary btn-sm shrink-0" @click="rotate">
          {{ rotating ? '발급 중…' : '토큰 재발급' }}
        </button>
      </div>
    </section>
  </div>
</template>
