import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { getDashboardSummary, getDashboardEvaluations, downloadReportPdf } from '../lib/api'

const VERDICT_COLORS = { Pass: '#4FD1C5', 'Needs Improvement': '#F5A623', Fail: '#E5484D' }

function StatCard({ label, value, accent }) {
  return (
    <div className="rounded-lg border border-base-border card-surface p-4">
      <p className="font-mono text-[10px] tracking-widest text-base-muted uppercase mb-1">{label}</p>
      <p className="font-display text-2xl font-semibold" style={accent ? { color: accent } : undefined}>{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [evaluations, setEvaluations] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState(null)

  const [filters, setFilters] = useState({
    date_from: '', date_to: '', mode: '', system_name: '', dataset_name: '', verdict_label: '',
  })

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, e] = await Promise.all([getDashboardSummary(filters), getDashboardEvaluations({ ...filters, limit: 100 })])
      setSummary(s)
      setEvaluations(e)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  const updateFilter = (key, value) => setFilters((f) => ({ ...f, [key]: value }))

  const handleExport = async () => {
    setExporting(true)
    setExportError(null)
    try {
      await downloadReportPdf(filters)
    } catch (err) {
      setExportError(err.message)
    } finally {
      setExporting(false)
    }
  }

  const verdictData = summary ? Object.entries(summary.verdict_counts).map(([name, value]) => ({ name, value })) : []
  const dimensionBarData = summary ? [
    { dimension: 'Relevance', avg: summary.avg_relevance }, { dimension: 'Accuracy', avg: summary.avg_accuracy },
    { dimension: 'Groundedness', avg: summary.avg_hallucination }, { dimension: 'Completeness', avg: summary.avg_completeness },
  ] : []

  if (error) {
    return (<div className="rounded-lg border border-signal-red/40 bg-signal-red/5 p-5"><p className="font-mono text-[11px] tracking-widest text-signal-red uppercase mb-1">Dashboard Error</p><p className="text-sm text-base-text">{error}</p></div>)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-lg border border-base-border card-surface p-4 flex flex-wrap gap-3 items-end">
        <div><label className="block font-mono text-[10px] text-base-muted uppercase tracking-widest mb-1">From</label>
          <input type="date" value={filters.date_from} onChange={(e) => updateFilter('date_from', e.target.value)} className="bg-base-panel2 border border-base-border rounded px-2 py-1.5 text-xs text-base-text" /></div>
        <div><label className="block font-mono text-[10px] text-base-muted uppercase tracking-widest mb-1">To</label>
          <input type="date" value={filters.date_to} onChange={(e) => updateFilter('date_to', e.target.value)} className="bg-base-panel2 border border-base-border rounded px-2 py-1.5 text-xs text-base-text" /></div>
        <div><label className="block font-mono text-[10px] text-base-muted uppercase tracking-widest mb-1">Mode</label>
          <select value={filters.mode} onChange={(e) => updateFilter('mode', e.target.value)} className="bg-base-panel2 border border-base-border rounded px-2 py-1.5 text-xs text-base-text">
            <option value="">All</option><option value="single">Single</option><option value="batch">Batch</option></select></div>
        <div><label className="block font-mono text-[10px] text-base-muted uppercase tracking-widest mb-1">System</label>
          <select value={filters.system_name} onChange={(e) => updateFilter('system_name', e.target.value)} className="bg-base-panel2 border border-base-border rounded px-2 py-1.5 text-xs text-base-text">
            <option value="">All</option>{summary?.available_systems.map((s) => (<option key={s} value={s}>{s}</option>))}</select></div>
        <div><label className="block font-mono text-[10px] text-base-muted uppercase tracking-widest mb-1">Dataset</label>
          <select value={filters.dataset_name} onChange={(e) => updateFilter('dataset_name', e.target.value)} className="bg-base-panel2 border border-base-border rounded px-2 py-1.5 text-xs text-base-text">
            <option value="">All</option>{summary?.available_datasets.map((d) => (<option key={d} value={d}>{d}</option>))}</select></div>
        <div><label className="block font-mono text-[10px] text-base-muted uppercase tracking-widest mb-1">Verdict</label>
          <select value={filters.verdict_label} onChange={(e) => updateFilter('verdict_label', e.target.value)} className="bg-base-panel2 border border-base-border rounded px-2 py-1.5 text-xs text-base-text">
            <option value="">All</option><option value="Pass">Pass</option><option value="Needs Improvement">Needs Improvement</option><option value="Fail">Fail</option></select></div>
        <button onClick={() => setFilters({ date_from: '', date_to: '', mode: '', system_name: '', dataset_name: '', verdict_label: '' })} className="text-xs font-mono text-base-muted hover:text-base-text underline underline-offset-2">Clear filters</button>
        <button onClick={handleExport} disabled={exporting || !summary || summary.total_evaluations === 0} className="ml-auto rounded-md bg-signal-teal disabled:bg-base-border disabled:text-base-muted disabled:cursor-not-allowed text-base-bg font-mono text-xs uppercase tracking-widest px-4 py-2 hover:brightness-110 transition-all">
          {exporting ? 'Generating PDF…' : 'Export PDF Report'}
        </button>
      </div>

      {exportError && (<div className="rounded-lg border border-signal-red/40 bg-signal-red/5 p-3"><p className="text-xs text-signal-red">{exportError}</p></div>)}

      {loading && <p className="text-sm text-base-muted">Loading dashboard…</p>}

      {!loading && summary && summary.total_evaluations === 0 && (
        <div className="rounded-lg border border-dashed border-base-border p-10 text-center"><p className="text-sm text-base-muted">No evaluations yet. Run a single or batch evaluation to see data here.</p></div>
      )}

      {!loading && summary && summary.total_evaluations > 0 && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Evaluations" value={summary.total_evaluations} />
            <StatCard label="Pass" value={summary.verdict_counts.Pass || 0} accent={VERDICT_COLORS.Pass} />
            <StatCard label="Needs Improvement" value={summary.verdict_counts['Needs Improvement'] || 0} accent={VERDICT_COLORS['Needs Improvement']} />
            <StatCard label="Fail" value={summary.verdict_counts.Fail || 0} accent={VERDICT_COLORS.Fail} />
            <StatCard label="Avg Relevance" value={summary.avg_relevance} />
            <StatCard label="Avg Accuracy" value={summary.avg_accuracy} />
            <StatCard label="Avg Completeness" value={summary.avg_completeness} />
            <StatCard label="Hallucination Frequency" value={`${summary.hallucination_frequency_pct}%`} accent={summary.hallucination_frequency_pct > 20 ? VERDICT_COLORS.Fail : undefined} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="rounded-lg border border-base-border card-surface p-5">
              <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-3">Verdict Distribution</p>
              <div style={{ width: '100%', height: 220 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={verdictData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                      {verdictData.map((entry) => (<Cell key={entry.name} fill={VERDICT_COLORS[entry.name] || '#8891A3'} />))}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#171C27', border: '1px solid #242B38', fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-lg border border-base-border card-surface p-5">
              <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-3">Average Score by Dimension</p>
              <div style={{ width: '100%', height: 220 }}>
                <ResponsiveContainer>
                  <BarChart data={dimensionBarData}>
                    <CartesianGrid stroke="#242B38" strokeDasharray="3 3" />
                    <XAxis dataKey="dimension" tick={{ fill: '#8891A3', fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#8891A3', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#171C27', border: '1px solid #242B38', fontSize: 12 }} />
                    <Bar dataKey="avg" fill="#5B8DEF" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-lg border border-base-border card-surface p-5 lg:col-span-2">
              <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-3">Quality Trend Over Time</p>
              <div style={{ width: '100%', height: 220 }}>
                <ResponsiveContainer>
                  <LineChart data={summary.quality_trend}>
                    <CartesianGrid stroke="#242B38" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: '#8891A3', fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#8891A3', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#171C27', border: '1px solid #242B38', fontSize: 12 }} />
                    <Line type="monotone" dataKey="avg_final_score" stroke="#4FD1C5" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-base-border card-surface overflow-hidden">
            <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase p-4 pb-2">Recent Evaluations ({evaluations.length})</p>
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-base-border text-base-muted font-mono text-[10px] uppercase tracking-widest">
                    <th className="text-left px-4 py-2">Date</th><th className="text-left px-4 py-2">Mode</th><th className="text-left px-4 py-2">System</th>
                    <th className="text-left px-4 py-2">Question</th><th className="text-right px-3 py-2">Final</th><th className="text-left px-4 py-2">Verdict</th>
                  </tr>
                </thead>
                <tbody>
                  {evaluations.slice(0, 50).map((ev) => (
                    <tr key={ev.id} className="border-b border-base-border/50 last:border-0">
                      <td className="px-4 py-2 text-base-muted font-mono">{ev.created_at.slice(0, 10)}</td>
                      <td className="px-4 py-2 text-base-muted">{ev.mode}</td>
                      <td className="px-4 py-2 text-base-muted">{ev.system_name}</td>
                      <td className="px-4 py-2 max-w-xs truncate" title={ev.question}>{ev.question}</td>
                      <td className="text-right px-3 py-2 font-mono">{Math.round(ev.final_score)}</td>
                      <td className="px-4 py-2 font-medium" style={{ color: VERDICT_COLORS[ev.verdict_label] }}>{ev.verdict_label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
