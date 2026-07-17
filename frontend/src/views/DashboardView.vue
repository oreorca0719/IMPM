<script setup>
import { computed, ref, watch } from 'vue'
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js'
import { Bar, Doughnut } from 'vue-chartjs'
import { useRoute, useRouter } from 'vue-router'
import { dashboardApi } from '../api'
import { STATUS_LABEL } from '../constants'
import { useProjectStore } from '../stores/project'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const project = useProjectStore()
const router = useRouter()
const route = useRoute()
const data = ref(null)

async function reload() {
  if (!project.current) return
  data.value = (await dashboardApi.get(project.current.id)).data
}
watch(() => project.current, (p) => { if (p) reload() }, { immediate: true })

const donutData = computed(() => {
  const sc = data.value?.status_counts || {}
  const keys = Object.keys(sc)
  return {
    labels: keys.map((k) => STATUS_LABEL[k] || k),
    datasets: [
      {
        data: keys.map((k) => sc[k]),
        backgroundColor: ['#cbd5e1', '#6366f1', '#22c55e', '#f59e0b', '#ef4444'],
      },
    ],
  }
})

const epicData = computed(() => ({
  labels: (data.value?.epic_progress || []).map((e) => e.epic_key),
  datasets: [
    {
      label: '진행률(%)',
      data: (data.value?.epic_progress || []).map((e) => e.percent),
      backgroundColor: '#6366f1',
    },
  ],
}))

const assigneeData = computed(() => {
  const rows = data.value?.assignee_load || []
  return {
    labels: rows.map((r) => r.user),
    datasets: [
      { label: '오픈', data: rows.map((r) => r.open), backgroundColor: '#f59e0b' },
      { label: '완료', data: rows.map((r) => r.done), backgroundColor: '#22c55e' },
    ],
  }
})

const barOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true } } }
const donutOpts = { responsive: true, maintainAspectRatio: false }

function openIssue(id) {
  router.replace({ query: { ...route.query, issue: id } })
}
</script>

<template>
  <div class="p-6 space-y-5">
    <h1 class="text-xl font-bold">진행률 대시보드</h1>

    <div v-if="data" class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <!-- 상태별 도넛 -->
      <section class="bg-white rounded-xl border border-slate-200 p-4">
        <h2 class="text-sm font-semibold mb-3 text-slate-600">상태별 이슈 수</h2>
        <div class="h-64"><Doughnut :data="donutData" :options="donutOpts" /></div>
      </section>

      <!-- 에픽 진행률 -->
      <section class="bg-white rounded-xl border border-slate-200 p-4">
        <h2 class="text-sm font-semibold mb-3 text-slate-600">에픽별 진행률</h2>
        <div class="h-64"><Bar :data="epicData" :options="barOpts" /></div>
      </section>

      <!-- 담당자 부하 -->
      <section class="bg-white rounded-xl border border-slate-200 p-4">
        <h2 class="text-sm font-semibold mb-3 text-slate-600">담당자별 오픈/완료</h2>
        <div class="h-64"><Bar :data="assigneeData" :options="barOpts" /></div>
      </section>

      <!-- 마감 임박 -->
      <section class="bg-white rounded-xl border border-slate-200 p-4">
        <h2 class="text-sm font-semibold mb-3 text-slate-600">마감 임박 (7일 이내)</h2>
        <ul class="divide-y divide-slate-100">
          <li
            v-for="i in data.due_soon"
            :key="i.id"
            class="flex items-center justify-between py-2 text-sm cursor-pointer hover:text-brand-600"
            @click="openIssue(i.id)"
          >
            <span><span class="font-mono text-xs text-slate-400 mr-2">{{ i.key }}</span>{{ i.title }}</span>
            <span class="text-amber-600">{{ i.due_date }}</span>
          </li>
          <li v-if="!data.due_soon.length" class="py-3 text-slate-400">임박한 이슈가 없습니다.</li>
        </ul>
      </section>
    </div>
    <div v-else class="text-slate-400">불러오는 중…</div>
  </div>
</template>
