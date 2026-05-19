const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function getApiBase() {
  return API_BASE
}

export async function getKpis(period = '2025') {
  const url = `${API_BASE}/api/kpis?period=${encodeURIComponent(period)}`
  const res = await fetch(url)
  if (res.status === 404) return null
  if (!res.ok) {
    const t = await res.text()
    throw new Error(t || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function uploadLedger(file) {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body,
  })
  let data = {}
  try {
    data = await res.json()
  } catch {
    /* ignore */
  }
  if (!res.ok) {
    const msg =
      typeof data.detail === 'string'
        ? data.detail
        : data.error ?? JSON.stringify(data.detail ?? data)
    throw new Error(msg || `Upload failed (${res.status})`)
  }
  return data
}

export async function postExplain(question) {
  const res = await fetch(`${API_BASE}/api/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  const text = await res.text()
  let data = {}
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { answer: text || 'Invalid response' }
  }
  return { ok: res.ok, status: res.status, data }
}
