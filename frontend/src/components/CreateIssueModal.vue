<script setup>
import { ref } from 'vue'
import { useProjectStore } from '../stores/project'
import { PRIORITIES } from '../constants'
import Icon from './Icon.vue'

defineProps({ epics: { type: Array, default: () => [] } })
const emit = defineEmits(['close', 'created'])
const project = useProjectStore()

const form = ref({
  title: '',
  priority: 'MEDIUM',
  assignee_id: null,
  epic_id: null,
  due_date: null,
})
const saving = ref(false)
const error = ref('')

async function submit() {
  if (!form.value.title.trim()) {
    error.value = '제목을 입력해 주세요.'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const payload = { ...form.value }
    if (!payload.assignee_id) delete payload.assignee_id
    if (!payload.epic_id) delete payload.epic_id
    if (!payload.due_date) delete payload.due_date
    emit('created', payload)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4"
    @click.self="emit('close')"
  >
    <div class="w-full max-w-md card soft-shadow p-6 space-y-5">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-semibold text-slate-900">새 이슈</h2>
        <button class="btn btn-ghost btn-xs !p-1.5" @click="emit('close')">
          <Icon name="close" :size="18" />
        </button>
      </div>

      <div>
        <label class="field-label">제목 <span class="text-red-500">*</span></label>
        <input
          v-model="form.title"
          class="input"
          placeholder="무엇을 해야 하나요?"
          autofocus
          @keyup.enter="submit"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="field-label">우선순위</label>
          <select v-model="form.priority" class="input">
            <option v-for="p in PRIORITIES" :key="p.key" :value="p.key">{{ p.label }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">담당자</label>
          <select v-model="form.assignee_id" class="input">
            <option :value="null">미지정</option>
            <option v-for="u in project.users" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">에픽</label>
          <select v-model="form.epic_id" class="input">
            <option :value="null">없음</option>
            <option v-for="e in epics" :key="e.id" :value="e.id">{{ e.key }} · {{ e.title }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">마감일</label>
          <input v-model="form.due_date" type="date" class="input" />
        </div>
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-1">
        <button class="btn btn-secondary btn-md" @click="emit('close')">취소</button>
        <button :disabled="saving" class="btn btn-primary btn-md" @click="submit">
          이슈 생성
        </button>
      </div>
    </div>
  </div>
</template>
