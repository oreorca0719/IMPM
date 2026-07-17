// 칸반 컬럼 구성 — 상태 enum 확장 시 여기만 수정(백엔드는 문자열 status 저장).
export const BOARD_COLUMNS = [
  { key: 'TODO', label: '할 일' },
  { key: 'IN_PROGRESS', label: '진행 중' },
  { key: 'DONE', label: '완료' },
]

export const STATUS_LABEL = Object.fromEntries(
  BOARD_COLUMNS.map((c) => [c.key, c.label]),
)

export const PRIORITIES = [
  { key: 'LOW', label: '낮음', color: '#94a3b8' },
  { key: 'MEDIUM', label: '보통', color: '#3b82f6' },
  { key: 'HIGH', label: '높음', color: '#f59e0b' },
  { key: 'URGENT', label: '긴급', color: '#ef4444' },
]

export const PRIORITY_MAP = Object.fromEntries(PRIORITIES.map((p) => [p.key, p]))
