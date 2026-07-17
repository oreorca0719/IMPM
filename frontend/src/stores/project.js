import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { labelApi, projectApi, userApi } from '../api'

// 1차는 단일~소수 프로젝트 — 첫 프로젝트를 현재 프로젝트로 사용.
export const useProjectStore = defineStore('project', () => {
  const current = ref(null)
  const users = ref([])
  const labels = ref([])
  const ready = ref(false)

  async function bootstrap() {
    const { data: projects } = await projectApi.list()
    current.value = projects[0] || null
    const { data: u } = await userApi.list()
    users.value = u
    if (current.value) {
      const { data: l } = await labelApi.list(current.value.id)
      labels.value = l
    }
    ready.value = true
  }

  async function refreshLabels() {
    if (!current.value) return
    const { data } = await labelApi.list(current.value.id)
    labels.value = data
  }

  const userMap = computed(() =>
    Object.fromEntries(users.value.map((u) => [u.id, u])),
  )
  const labelMap = computed(() =>
    Object.fromEntries(labels.value.map((l) => [l.id, l])),
  )

  return { current, users, labels, ready, bootstrap, refreshLabels, userMap, labelMap }
})
