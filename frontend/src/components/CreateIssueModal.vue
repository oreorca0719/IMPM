<script setup>
import { ref } from 'vue'
import { useProjectStore } from '../stores/project'
import { PRIORITIES } from '../constants'

const props = defineProps({
  epics: { type: Array, default: () => [] },
})
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
  <div class="fixed inset-0 z-40 flex items-center justify-center bg-black/40" @click.self="emit('close')">
    <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl space-y-4">
      <h2 class="text-lg font-semibold">새 이슈</h2>

      <div class="space-y-1">
        <label class="text-sm text-slate-600">제목 *</label>
        <input
          v-model="form.title"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-brand-500"
          placeholder="무엇을 해야 하나요?"
          @keyup.enter="submit"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="space-y-1">
          <label class="text-sm text-slate-600">우선순위</label>
          <select v-model="form.priority" class="w-full rounded-lg border border-slate-300 px-2 py-2">
            <option v-for="p in PRIORITIES" :key="p.key" :value="p.key">{{ p.label }}</option>
          </select>
        </div>
        <div class="space-y-1">
          <label class="text-sm text-slate-600">담당자</label>
          <select v-model="form.assignee_id" class="w-full rounded-lg border border-slate-300 px-2 py-2">
            <option :value="null">미지정</option>
            <option v-for="u in project.users" :key="u.id" :value="u.id">{{ u.name }}</option>
          </select>
        </div>
        <div class="space-y-1">
          <label class="text-sm text-slate-600">에픽</label>
          <select v-model="form.epic_id" class="w-full rounded-lg border border-slate-300 px-2 py-2">
            <option :value="null">없음</option>
            <option v-for="e in epics" :key="e.id" :value="e.id">{{ e.key }} · {{ e.title }}</option>
          </select>
        </div>
        <div class="space-y-1">
          <label class="text-sm text-slate-600">마감일</label>
          <input v-model="form.due_date" type="date" class="w-full rounded-lg border border-slate-300 px-2 py-2" />
        </div>
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-2">
        <button class="rounded-lg px-4 py-2 text-slate-600 hover:bg-slate-100" @click="emit('close')">취소</button>
        <button
          :disabled="saving"
          class="rounded-lg bg-brand-600 px-4 py-2 text-white hover:bg-brand-700 disabled:opacity-60"
          @click="submit"
        >
          생성
        </button>
      </div>
    </div>
  </div>
</template>
