// 백엔드는 시각을 naive UTC(오프셋 없음)로 저장한다.
// 오프셋이 없으면 UTC로 간주(Z 부착)하고, 로컬(KST 등)로 표시한다.
function toUtc(ts) {
  if (!ts) return null
  const hasTz = /[zZ]$|[+-]\d\d:?\d\d$/.test(ts)
  return new Date(hasTz ? ts : ts + 'Z')
}

export function fmtDateTime(ts) {
  const d = toUtc(ts)
  if (!d) return ''
  return d.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' })
}

export function fmtDate(ts) {
  const d = toUtc(ts)
  if (!d) return ''
  return d.toLocaleDateString('ko-KR', { dateStyle: 'medium' })
}
