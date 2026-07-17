<script setup>
import { onMounted, ref, watch } from 'vue'
import { commentApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { useProjectStore } from '../stores/project'
import { fmtDateTime } from '../utils/datetime'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({ issueId: { type: Number, required: true } })
const emit = defineEmits(['changed'])
const auth = useAuthStore()
const project = useProjectStore()

const comments = ref([])
const body = ref('')
const editingId = ref(null)
const editBody = ref('')

async function load() {
  comments.value = (await commentApi.list(props.issueId)).data
}
onMounted(load)
watch(() => props.issueId, load)

async function add() {
  if (!body.value.trim()) return
  await commentApi.create(props.issueId, body.value)
  body.value = ''
  await load()
  emit('changed')
}
function startEdit(c) {
  editingId.value = c.id
  editBody.value = c.body
}
async function saveEdit() {
  await commentApi.update(editingId.value, editBody.value)
  editingId.value = null
  await load()
}
async function remove(c) {
  await commentApi.remove(c.id)
  await load()
  emit('changed')
}
const name = (id) => project.userMap[id]?.name || '알 수 없음'
</script>

<template>
  <div class="space-y-4">
    <div v-if="!comments.length" class="text-sm text-slate-400 py-2">
      첫 댓글을 남겨보세요.
    </div>

    <div v-for="c in comments" :key="c.id" class="flex gap-2.5">
      <UserAvatar :name="name(c.author_id)" :size="30" />
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 text-xs">
          <span class="font-medium text-slate-700">{{ name(c.author_id) }}</span>
          <span class="text-slate-400">{{ fmtDateTime(c.created_at) }}</span>
          <template v-if="c.author_id === auth.user?.id">
            <button class="text-slate-400 hover:text-indigo-600" @click="startEdit(c)">수정</button>
            <button class="text-slate-400 hover:text-red-600" @click="remove(c)">삭제</button>
          </template>
        </div>
        <div v-if="editingId === c.id" class="mt-1.5 space-y-1.5">
          <textarea v-model="editBody" rows="2" class="input" />
          <div class="flex gap-2">
            <button class="btn btn-primary btn-xs" @click="saveEdit">저장</button>
            <button class="btn btn-ghost btn-xs" @click="editingId = null">취소</button>
          </div>
        </div>
        <p v-else class="mt-1 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
          {{ c.body }}
        </p>
      </div>
    </div>

    <div class="flex gap-2 pt-3 border-t border-slate-100">
      <textarea
        v-model="body"
        rows="2"
        placeholder="댓글 작성…"
        class="input resize-none"
        @keydown.meta.enter="add"
        @keydown.ctrl.enter="add"
      />
      <button class="btn btn-primary btn-sm self-end" @click="add">등록</button>
    </div>
  </div>
</template>
