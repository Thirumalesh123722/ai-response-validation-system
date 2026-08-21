import { useState, useRef, useCallback } from 'react'
import { startBatchJob, getBatchStatus } from '../lib/api'

const VERDICT_COLOR = { Pass: 'text-signal-teal', 'Needs Improvement': 'text-signal-amber', Fail: 'text-signal-red' }

function BatchRow({ row }) {
  const [expanded, setExpanded] = useState(false)
  if (row.error) {
    return (
      <tr className="border-b border-base-border/50 last:border-0">
        <td className="px-4 py-3 text-base-muted font-mono">{row.row_index + 1}</td>
        <td className="px-4 py-3 max-w-xs truncate" title={row.question}>{row.question}</td>
        <td colSpan={6} className="px-3 py-3 text-signal-red">Error: {row.error}</td>
      </tr>
    )
  }
  const r = row.result
  return (
    <>
      <tr className="border-b border-base-border/50 last:border-0 cursor-pointer hover:bg-base-panel2/50 transition-colors" onClick={() => setExpanded((v) => !v)}>
        <td className="px-4 py-3 text-base-muted font-mono"><span className="inline-block w-3 text-base-muted">{expanded ? '▾' : '▸'}</span>{row.row_index + 1}</td>
        <td className="px-4 py-3 max-w-xs truncate" title={row.question}>{row.question}</td>
        <td className="text-right px-3 py-3 font-mono">{Math.round(r.relevance_score)}</td>
        <td className="text-right px-3 py-3 font-mono">{Math.round(r.accuracy_score)}</td>
        <td className="text-right px-3 py-3 font-mono">{Math.round(r.hallucination_score)}</td>
        <td className="text-right px-3 py-3 font-mono">{Math.round(r.completeness_score)}</td>
        <td className="text-right px-3 py-3 font-mono font-semibold">{Math.round(r.final_score)}</td>
        <td className={`px-4 py-3 font-medium ${VERDICT_COLOR[r.verdict_label] || ''}`}>{r.verdict_label}</td>
      </tr>
      {expanded && (
        <tr className="border-b border-base-border/50 last:border-0 bg-base-panel2/30">
          <td colSpan={8} className="px-4 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div><p className="font-mono text-[10px] tracking-widest text-base-muted uppercase mb-1">AI Response</p><p className="text-base-text leading-relaxed">{row.ai_response}</p></div>
              <div><p className="font-mono text-[10px] tracking-widest text-base-muted uppercase mb-1">Consolidated Reasoning</p><p className="text-base-muted leading-relaxed">{r.verdict}</p></div>
              <div>
                <p className="font-mono text-[10px] tracking-widest text-signal-red uppercase mb-1">Hallucination Findings {r.hallucination_flags?.length ? `(${r.hallucination_flags.length})` : '(none)'}</p>
                {r.hallucination_flags && r.hallucination_flags.length > 0 ? (
                  <ul className="space-y-1">{r.hallucination_flags.map((flag, i) => (<li key={i} className="text-base-text flex gap-1.5"><span className="text-signal-red">▲</span><span>{flag}</span></li>))}</ul>
                ) : (<p className="text-base-muted">{r.hallucination_reasoning}</p>)}
              </div>
              <div>
                <p className="font-mono text-[10px] tracking-widest text-base-muted uppercase mb-1">Per-Dimension Reasoning</p>
                <ul className="space-y-1 text-base-muted">
                  <li><span className="text-base-text">Relevance:</span> {r.relevance_reasoning}</li>
                  <li><span className="text-base-text">Accuracy:</span> {r.accuracy_reasoning}</li>
                  <li><span className="text-base-text">Completeness:</span> {r.completeness_reasoning}</li>
                </ul>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function BatchEvaluation() {
  const [job, setJob] = useState(null)
  const [error, setError] = useState(null)
  const [fileName, setFileName] = useState('')
  const [systemName, setSystemName] = useState('')
  const [datasetName, setDatasetName] = useState('')
  const pollRef = useRef(null)

  const stopPolling = useCallback(() => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null } }, [])

  const poll = useCallback((jobId) => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const status = await getBatchStatus(jobId)
        setJob(status)
        if (status.status === 'done') stopPolling()
      } catch (err) { setError(err.message); stopPolling() }
    }, 1500)
  }, [stopPolling])

  const handleFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setFileName(file.name); setError(null); setJob(null)
    try {
      const { job_id, total } = await startBatchJob(file, systemName.trim() || 'Unspecified', datasetName.trim() || null)
      setJob({ job_id, total, completed: 0, status: 'running', rows: [] })
      poll(job_id)
    } catch (err) { setError(err.message) }
  }

  const progressPct = job ? Math.round((job.completed / Math.max(job.total, 1)) * 100) : 0

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">AI system name <span className="text-base-muted/60 normal-case">(optional)</span></label>
          <input type="text" value={systemName} onChange={(e) => setSystemName(e.target.value)} placeholder="e.g. System A"
            className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2 text-sm text-base-text placeholder:text-base-muted/60 focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue" />
        </div>
        <div>
          <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">Dataset label <span className="text-base-muted/60 normal-case">(optional)</span></label>
          <input type="text" value={datasetName} onChange={(e) => setDatasetName(e.target.value)} placeholder="defaults to filename"
            className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2 text-sm text-base-text placeholder:text-base-muted/60 focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue" />
        </div>
      </div>

      <div>
        <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-2">CSV file</p>
        <p className="text-xs text-base-muted mb-3 leading-relaxed">
          Columns required: <code className="text-base-text">question</code>, <code className="text-base-text">ai_response</code>. Optional: <code className="text-base-text">reference_answer</code>.
        </p>
        <label className="cursor-pointer inline-block rounded-md border border-dashed border-base-border px-4 py-2.5 text-xs text-base-muted hover:border-signal-blue hover:text-base-text transition-colors">
          <input type="file" accept=".csv" onChange={handleFile} className="hidden" />
          Choose CSV file
        </label>
        {fileName && <span className="ml-3 text-xs font-mono text-base-muted">{fileName}</span>}
      </div>

      {error && (<div className="rounded-lg border border-signal-red/40 bg-signal-red/5 p-4"><p className="font-mono text-[11px] tracking-widest text-signal-red uppercase mb-1">Batch Error</p><p className="text-sm text-base-text">{error}</p></div>)}

      {job && (
        <div className="rounded-lg border border-base-border card-surface p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase">{job.status === 'done' ? 'Batch complete' : 'Processing…'}</p>
            <span className="font-mono text-xs text-base-muted">{job.completed}/{job.total}</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-base-border overflow-hidden"><div className="h-full bg-signal-teal transition-all duration-500" style={{ width: `${progressPct}%` }} /></div>
          {job.status !== 'done' && <p className="text-[11px] text-base-muted mt-2">Each row takes ~15-20s due to API pacing across 5 agent calls. Hang tight.</p>}
        </div>
      )}

      {job && job.rows && job.rows.length > 0 && (
        <div className="rounded-lg border border-base-border card-surface overflow-hidden">
          <div className="px-4 py-2 border-b border-base-border"><p className="text-[11px] text-base-muted">Click a row to see the full response, hallucination findings, and reasoning.</p></div>
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-base-border text-base-muted font-mono text-[10px] uppercase tracking-widest">
                  <th className="text-left px-4 py-3">#</th><th className="text-left px-4 py-3">Question</th>
                  <th className="text-right px-3 py-3">Rel</th><th className="text-right px-3 py-3">Acc</th>
                  <th className="text-right px-3 py-3">Ground</th><th className="text-right px-3 py-3">Comp</th>
                  <th className="text-right px-3 py-3">Final</th><th className="text-left px-4 py-3">Verdict</th>
                </tr>
              </thead>
              <tbody>{[...job.rows].sort((a, b) => a.row_index - b.row_index).map((row) => (<BatchRow key={row.row_index} row={row} />))}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
