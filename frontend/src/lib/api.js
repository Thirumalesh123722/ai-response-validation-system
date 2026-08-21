import { authFetch } from './auth'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // ignore parse failure
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function checkHealth() {
  // /health is intentionally unauthenticated (liveness check), so plain fetch is fine.
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const res = await fetch(`${BASE_URL}/health`)
  return handle(res)
}

export async function evaluateResponse(payload) {
  const res = await authFetch('/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handle(res)
}

export async function ingestDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await authFetch('/ingest', { method: 'POST', body: formData })
  return handle(res)
}

export async function startBatchJob(file, systemName = 'Unspecified', datasetName = null) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('system_name', systemName)
  if (datasetName) formData.append('dataset_name', datasetName)
  const res = await authFetch('/batch/upload', { method: 'POST', body: formData })
  return handle(res)
}

export async function getBatchStatus(jobId) {
  const res = await authFetch(`/batch/status/${jobId}`)
  return handle(res)
}

export async function getDashboardSummary(filters = {}) {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v))
  const res = await authFetch(`/dashboard/summary?${params.toString()}`)
  return handle(res)
}

export async function getDashboardEvaluations(filters = {}) {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v))
  const res = await authFetch(`/dashboard/evaluations?${params.toString()}`)
  return handle(res)
}

export async function downloadReportPdf(filters = {}) {
  const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v))
  const res = await authFetch(`/report/pdf?${params.toString()}`)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="(.+)"/)
  a.download = match ? match[1] : 'evaluation_report.pdf'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}
