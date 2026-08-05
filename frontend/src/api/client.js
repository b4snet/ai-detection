const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const ASSET_BASE = BASE.endsWith('/api') ? BASE.slice(0, -4) : BASE

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} ${detail}`)
  }
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : res
}

export const api = {
  status: () => request('/status'),
  capabilities: () => request('/capabilities'),

  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('/analysis/upload', { method: 'POST', body: fd })
  },

  analysis: (id) => request(`/analysis/${id}`),
  analyses: () => request('/analysis/'),
  run: (id) => request(`/analysis/${id}/run`, { method: 'POST' }),

  search: (q, limit = 10) =>
    request(`/search/osint?q=${encodeURIComponent(q)}&limit=${limit}`),
  searchEntities: (q) =>
    request(`/search/entities?q=${encodeURIComponent(q)}`),

  logs: (limit = 120) => request(`/logs/?limit=${limit}`),

  reportPdf: (id) => `${BASE}/reports/${id}/pdf`,
  reportJson: (id) => `${BASE}/reports/${id}/json`,
}

export function analysisImage(analysis) {
  if (!analysis || !analysis.id) return null
  return `${ASSET_BASE}/uploads/${analysis.filename}`
}
