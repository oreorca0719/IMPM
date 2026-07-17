<script setup>
import { onMounted, ref, watch } from 'vue'
import { epicApi, issueApi } from '../api'
import { BOARD_COLUMNS, PRIORITIES } from '../constants'
import { useIssueStore } from '../stores/issue'
import { useProjectStore } from '../stores/project'
import ActivityFeed from './ActivityFeed.vue'
import CommentThread from './CommentThread.vue'
import LabelChip from './LabelChip.vue'

const props = defineProps({ issueId: { type: Number, required: true } })
const emit = defineEmits(['close'])

const project = useProjectStore()
const issueStore = useIssueStore()

const issue = ref(null)
const epics = ref([])
const tab = ref('comments')
const addLabelId = ref(null)

async function load() {
  const { data } = await issueApi.get(props.issueId)
  issue.value = data
  if (project.current) epics.value = (await epicApi.list(project.current.id)).data
}
onMounted(load)
watch(() => props.issueId, load)

async function save(patch) {
  const { data } = await issueApi.update(props.issueId, patch)
  issue.value = data
  issueStore.replace(data)
}

async function attachLabel() {
  if (!addLabelId.value) return
  const { data } = await issueApi.addLabel(props.issueId, addLabelId.value)
  issue.value = data
  issueStore.replace(data)
  addLabelId.value = null
}
async function detachLabel(labelId) {
  const { data } = await issueApi.removeLabel(props.issueId, labelId)
  issue.value = data
  issueStore.replace(data)
}

async function removeIssue() {
  if (!confirm('이 이슈를 삭제할까요?')) return
  await issueApi.remove(props.issueId)
  issueStore.removeLocal(props.issueId)
  emit('close')
}

function availableLabels() {
  const attached = new Set((issue.value?.labels || []).map((l) => l.id))
  return project.labels.filter((l) => !attached.has(l.id))
}
</script>

<template>
  <div class="fixed inset-0 z-30 flex justify-end bg-black/30" @click.self="emit('close')">
    <div class="w-full max-w-lg h-full overflow-auto bg-white shadow-2xl">
      <div v-if="issue" class="p-6 space-y-5">
        <!-- 헤더 -->
        <div class="flex items-center justify-between">
          <span class="font-mono text-sm text-slate-400">{{ issue.key }}</span>
          <div class="flex items-center gap-3">
            <button class="text-sm text-red-500 hover:text-red-700" @click="removeIssue">삭제</button>
            <button class="text-slate-400 hover:text-slate-700 text-xl leading-none" @click="emit('close')">×</button>
          </div>
        </div>

        <!-- 제목 -->
        <input
          :value="issue.title"
          class="w-full text-lg font-semibold outline-none border-b border-transparent focus:border-brand-400 py-1"
          @change="(e) => save({ title: e.target.value })"
        />

        <!-- 속성 그리드 -->
        <div class="grid grid-cols-2 gap-3 text-sm">
          <label class="space-y-1">
            <span class="text-slate-500">상태</span>
            <select
              :value="issue.status"
              class="w-full rounded border border-slate-300 px-2 py-1.5"
              @change="(e) => save({ status: e.target.value })"
            >
              <option v-for="c in BOARD_COLUMNS" :key="c.key" :value="c.key">{{ c.label }}</option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="text-slate-500">우선순위</span>
            <select
              :value="issue.priority"
              class="w-full rounded border border-slate-300 px-2 py-1.5"
              @change="(e) => save({ priority: e.target.value })"
            >
              <option v-for="p in PRIORITIES" :key="p.key" :value="p.key">{{ p.label }}</option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="text-slate-500">담당자</span>
            <select
              :value="issue.assignee_id ?? ''"
              class="w-full rounded border border-slate-300 px-2 py-1.5"
              @change="(e) => save({ assignee_id: e.target.value ? Number(e.target.value) : null })"
            >
              <option value="">미지정</option>
              <option v-for="u in project.users" :key="u.id" :value="u.id">{{ u.name }}</option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="text-slate-500">마감일</span>
            <input
              type="date"
              :value="issue.due_date ?? ''"
              class="w-full rounded border border-slate-300 px-2 py-1.5"
              @change="(e) => save({ due_date: e.target.value || null })"
            />
          </label>
          <label class="space-y-1 col-span-2">
            <span class="text-slate-500">에픽</span>
            <select
              :value="issue.epic_id ?? ''"
              class="w-full rounded border border-slate-300 px-2 py-1.5"
              @change="(e) => save({ epic_id: e.target.value ? Number(e.target.value) : null })"
            >
              <option value="">없음</option>
              <option v-for="ep in epics" :key="ep.id" :value="ep.id">{{ ep.key }} · {{ ep.title }}</option>
            </select>
          </label>
        </div>

        <!-- 라벨 -->
        <div class="space-y-2">
          <span class="text-sm text-slate-500">라벨</span>
          <div class="flex flex-wrap items-center gap-1">
            <LabelChip
              v-for="l in issue.labels"
              :key="l.id"
              :label="l"
              removable
              @remove="detachLabel(l.id)"
            />
            <select v-model="addLabelId" class="rounded border border-slate-300 px-2 py-1 text-xs" @change="attachLabel">
              <option :value="null">+ 라벨</option>
              <option v-for="l in availableLabels()" :key="l.id" :value="l.id">{{ l.name }}</option>
            </select>
          </div>
        </div>

        <!-- 설명 -->
        <div class="space-y-1">
          <span class="text-sm text-slate-500">설명</span>
          <textarea
            :value="issue.description ?? ''"
            rows="4"
            class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="설명 추가…"
            @change="(e) => save({ description: e.target.value })"
          />
        </div>

        <!-- 탭 -->
        <div class="border-b border-slate-200 flex gap-4 text-sm">
          <button
            class="pb-2 -mb-px border-b-2"
            :class="tab === 'comments' ? 'border-brand-600 text-brand-600 font-medium' : 'border-transparent text-slate-500'"
            @click="tab = 'comments'"
          >
            댓글 <span v-if="issue.comment_count">({{ issue.comment_count }})</span>
          </button>
          <button
            class="pb-2 -mb-px border-b-2"
            :class="tab === 'activity' ? 'border-brand-600 text-brand-600 font-medium' : 'border-transparent text-slate-500'"
            @click="tab = 'activity'"
          >
            활동
          </button>
        </div>

        <CommentThread v-if="tab === 'comments'" :issue-id="issueId" @changed="load" />
        <ActivityFeed v-else :issue-id="issueId" :key="issue.updated_at" />
      </div>

      <div v-else class="p-6 text-slate-400">불러오는 중…</div>
    </div>
  </div>
</template>
