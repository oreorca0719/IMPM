import { defineStore } from 'pinia'
import { ref } from 'vue'
import { issueApi } from '../api'

export const useIssueStore = defineStore('issue', () => {
  const issues = ref([])
  const loading = ref(false)

  async function load(pid, params = {}) {
    loading.value = true
    try {
      const { data } = await issueApi.list(pid, params)
      issues.value = data
    } finally {
      loading.value = false
    }
  }

  async function create(pid, payload) {
    const { data } = await issueApi.create(pid, payload)
    // 상세(라벨 포함) 응답 → 보드용 축약본 반영
    issues.value.push(data)
    return data
  }

  function replace(updated) {
    const i = issues.value.findIndex((x) => x.id === updated.id)
    if (i !== -1) issues.value[i] = { ...issues.value[i], ...updated }
  }

  function removeLocal(id) {
    issues.value = issues.value.filter((x) => x.id !== id)
  }

  // 낙관적 이동: 즉시 UI 반영 후 API 확정, 실패 시 롤백.
  async function move(issue, status, boardOrder) {
    const prev = { status: issue.status, board_order: issue.board_order }
    issue.status = status
    issue.board_order = boardOrder
    try {
      const { data } = await issueApi.move(issue.id, status, boardOrder)
      replace(data)
    } catch (e) {
      issue.status = prev.status
      issue.board_order = prev.board_order
      throw e
    }
  }

  return { issues, loading, load, create, replace, removeLocal, move }
})
