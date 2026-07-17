<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import Icon from './Icon.vue'
import LabelChip from './LabelChip.vue'
import PriorityBadge from './PriorityBadge.vue'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({ issue: { type: Object, required: true } })
const project = useProjectStore()
const router = useRouter()
const route = useRoute()

const assignee = computed(() =>
  props.issue.assignee_id ? project.userMap[props.issue.assignee_id] : null,
)

const dueInfo = computed(() => {
  if (!props.issue.due_date) return null
  const due = new Date(props.issue.due_date)
  const days = Math.ceil((due - new Date()) / 86400000)
  return { text: props.issue.due_date.slice(5), soon: days <= 7, over: days < 0 }
})

function open() {
  router.replace({ query: { ...route.query, issue: props.issue.id } })
}
</script>

<template>
  <div
    class="group bg-white rounded-lg border border-slate-200 p-3 cursor-pointer space-y-2
      transition-all duration-150 hover:border-slate-300 hover:shadow-md"
    @click="open"
  >
    <div class="flex items-center justify-between">
      <span class="text-[11px] font-mono font-medium text-slate-400">{{ issue.key }}</span>
      <PriorityBadge :priority="issue.priority" dot />
    </div>

    <div class="text-sm font-medium text-slate-800 leading-snug">{{ issue.title }}</div>

    <div v-if="issue.labels?.length" class="flex flex-wrap gap-1">
      <LabelChip v-for="l in issue.labels" :key="l.id" :label="l" />
    </div>

    <div class="flex items-center justify-between pt-0.5">
      <span
        v-if="dueInfo"
        class="inline-flex items-center gap-1 text-[11px] font-medium"
        :class="dueInfo.over ? 'text-red-500' : dueInfo.soon ? 'text-amber-500' : 'text-slate-400'"
      >
        <Icon name="calendar" :size="13" /> {{ dueInfo.text }}
      </span>
      <span v-else />
      <UserAvatar v-if="assignee" :name="assignee.name" :size="22" />
      <span
        v-else
        class="h-[22px] w-[22px] rounded-full border border-dashed border-slate-300"
      />
    </div>
  </div>
</template>
