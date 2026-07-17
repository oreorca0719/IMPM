<script setup>
import { onMounted, ref } from 'vue'

// P0 스캐폴드 검증용 랜딩 — 백엔드 /api/health 프록시 연결 확인.
const health = ref('확인 중…')

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    const data = await res.json()
    health.value = data.status === 'ok' ? `연결됨 (${data.app})` : '응답 이상'
  } catch (e) {
    health.value = '백엔드 미연결'
  }
})
</script>

<template>
  <main class="min-h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
    <h1 class="text-4xl font-bold text-brand-600">IMPM</h1>
    <p class="text-slate-500">STRIPE 개발 프로젝트 관리 도구</p>
    <span class="rounded-full bg-white px-4 py-1 text-sm shadow ring-1 ring-slate-200">
      API: {{ health }}
    </span>
  </main>
</template>
