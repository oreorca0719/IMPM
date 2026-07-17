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
import Icon from '../components/Icon.vue'
import { fmtDate } from '../utils/datetime'

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

const kpi = computed(() => {
  const sc = data.value?.status_counts || {}
  const total = Object.values(sc).reduce((a, b) => a + b, 0)
  const done = sc.DONE || 0
  const open = total - done
  return {
    total,
    open,
    done,
    percent: total ? Math.round((done / total) * 100) : 0,
    dueSoon: data.value?.due_soon?.length || 0,
  }
})

const donutData = computed(() => {
  const sc = data.value?.status_counts || {}
  const keys = Object.keys(sc)
  return {
    labels: keys.map((k) => STATUS_LABEL[k] || k),
    datasets: [
      {
        data: keys.map((k) => sc[k]),
        backgroundColor: ['#cbd5e1', '#6366f1', '#22c55e', '#f59e0b', '#ef4444'],
        borderWidth: 0,
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
      borderRadius: 6,
      maxBarThickness: 26,
    },
  ],
}))

const assigneeData = computed(() => {
  const rows = data.value?.assignee_load || []
  return {
    labels: rows.map((r) => r.user),
    datasets: [
      { label: '오픈', data: rows.map((r) => r.open), backgroundColor: '#f59e0b', borderRadius: 5, maxBarThickness: 22 },
      { label: '완료', data: rows.map((r) => r.done), backgroundColor: '#22c55e', borderRadius: 5, maxBarThickness: 22 },
    ],
  }
})

const barOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: true, labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true } } },
  scales: { x: { grid: { display: false } }, y: { grid: { color: '#f1f5f9' }, ticks: { precision: 0 } } },
}
const donutOpts = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '62%',
  plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, padding: 14 } } },
}

function openIssue(id) {
  router.replace({ query: { ...route.query, issue: id } })
}
</script>

<template>
  <div class="px-8 py-6 space-y-5">
    <header>
      <h1 class="text-xl font-semibold text-slate-900">대시보드</h1>
      <p class="text-sm text-slate-400 mt-0.5">프로젝트 진행 현황 한눈에</p>
    </header>

    <template v-if="data">
      <!-- KPI -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="card p-4">
          <div class="text-xs text-slate-400">전체 이슈</div>
          <div class="text-2xl font-semibold text-slate-900 mt-1 tabular-nums">{{ kpi.total }}</div>
        </div>
        <div class="card p-4">
          <div class="text-xs text-slate-400">진행/대기</div>
          <div class="text-2xl font-semibold text-indigo-600 mt-1 tabular-nums">{{ kpi.open }}</div>
        </div>
        <div class="card p-4">
          <div class="text-xs text-slate-400">완료율</div>
          <div class="text-2xl font-semibold text-green-600 mt-1 tabular-nums">{{ kpi.percent }}%</div>
        </div>
        <div class="card p-4">
          <div class="text-xs text-slate-400">마감 임박(7일)</div>
          <div class="text-2xl font-semibold text-amber-600 mt-1 tabular-nums">{{ kpi.dueSoon }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <section class="card p-5">
          <h2 class="text-sm font-semibold text-slate-700 mb-4">상태별 이슈 수</h2>
          <div class="h-60"><Doughnut :data="donutData" :options="donutOpts" /></div>
        </section>

        <section class="card p-5">
          <h2 class="text-sm font-semibold text-slate-700 mb-4">에픽별 진행률</h2>
          <div class="h-60"><Bar :data="epicData" :options="barOpts" /></div>
        </section>

        <section class="card p-5">
          <h2 class="text-sm font-semibold text-slate-700 mb-4">담당자별 오픈/완료</h2>
          <div class="h-60"><Bar :data="assigneeData" :options="barOpts" /></div>
        </section>

        <section class="card p-5">
          <h2 class="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-1.5">
            <Icon name="clock" :size="15" class="text-amber-500" /> 마감 임박 (7일 이내)
          </h2>
          <ul class="divide-y divide-slate-50">
            <li
              v-for="i in data.due_soon"
              :key="i.id"
              class="flex items-center justify-between py-2.5 text-sm cursor-pointer hover:bg-slate-50 -mx-2 px-2 rounded-lg transition-colors"
              @click="openIssue(i.id)"
            >
              <span class="min-w-0 truncate">
                <span class="font-mono text-xs text-slate-400 mr-2">{{ i.key }}</span>
                <span class="text-slate-700">{{ i.title }}</span>
              </span>
              <span class="text-amber-600 text-xs font-medium shrink-0">{{ fmtDate(i.due_date) }}</span>
            </li>
            <li v-if="!data.due_soon.length" class="py-6 text-center text-slate-400 text-sm">
              임박한 이슈가 없습니다.
            </li>
          </ul>
        </section>
      </div>
    </template>

    <div v-else class="card p-10 text-center text-slate-400 text-sm">불러오는 중…</div>
  </div>
</template>
