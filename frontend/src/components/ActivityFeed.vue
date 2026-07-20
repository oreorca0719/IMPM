<script setup>
import { onMounted, ref, watch } from 'vue'
import { commentApi } from '../api'
import { useProjectStore } from '../stores/project'
import { PRIORITY_MAP, STATUS_LABEL } from '../constants'
import { fmtDateTime } from '../utils/datetime'

const props = defineProps({ issueId: { type: Number, required: true } })
const project = useProjectStore()
const logs = ref([])

async function load() {
  logs.value = (await commentApi.activity(props.issueId)).data
}
onMounted(load)
watch(() => props.issueId, load)

const actor = (id) => project.userMap[id]?.name || '누군가'
const statusText = (v) => (v ? STATUS_LABEL[v] || v : '없음')
const priorityText = (v) => (v ? PRIORITY_MAP[v]?.label || v : '없음')
const userText = (id) => (id ? project.userMap[Number(id)]?.name || `#${id}` : '미지정')

function describe(log) {
  const who = actor(log.actor_id)
  switch (log.action) {
    case 'created':
      return `${who}이(가) 이슈를 생성했습니다.`
    case 'status_changed':
      return `${who}이(가) 상태를 ${statusText(log.old_value)} → ${statusText(log.new_value)} 로 변경했습니다.`
    case 'assignee_changed':
      return `${who}이(가) 담당자를 ${userText(log.old_value)} → ${userText(log.new_value)} 로 변경했습니다.`
    case 'due_changed':
      return `${who}이(가) 마감일을 ${log.old_value || '없음'} → ${log.new_value || '없음'} 로 변경했습니다.`
    case 'priority_changed':
      return `${who}이(가) 우선순위를 ${priorityText(log.old_value)} → ${priorityText(log.new_value)} 로 변경했습니다.`
    case 'epic_changed':
      return `${who}이(가) 에픽을 변경했습니다.`
    case 'reporter_changed':
      return `${who}이(가) 등록자를 ${userText(log.old_value)} → ${userText(log.new_value)} 로 정정했습니다.`
    default:
      return `${who}이(가) ${log.action}`
  }
}
</script>

<template>
  <div>
    <div v-if="!logs.length" class="text-sm text-slate-400 py-2">활동 내역이 없습니다.</div>
    <ol class="relative border-l border-slate-200 ml-1.5 space-y-4">
      <li v-for="log in logs" :key="log.id" class="pl-4 relative">
        <span class="absolute -left-[5px] top-1.5 h-2 w-2 rounded-full bg-indigo-400 ring-2 ring-white" />
        <p class="text-sm text-slate-700 leading-snug">{{ describe(log) }}</p>
        <p class="text-xs text-slate-400 mt-0.5">{{ fmtDateTime(log.created_at) }}</p>
      </li>
    </ol>
  </div>
</template>
