import Gauge from './Gauge'
const LABEL_COLOR = { Pass: '#4FD1C5', 'Needs Improvement': '#F5A623', Fail: '#E5484D' }
export default function VerdictBanner({ finalScore, verdictLabel, verdict }) {
  const color = LABEL_COLOR[verdictLabel] || '#8891A3'
  return (
    <div className="rounded-lg border border-base-border card-surface bg-gradient-to-br from-base-panel2 to-base-panel p-6 flex items-center gap-8 flex-wrap">
      <Gauge score={finalScore} size={168} strokeWidth={14} />
      <div className="flex-1 min-w-[240px]">
        <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase">Final Weighted Score</p>
        <h2 className="font-display text-2xl font-semibold mt-1" style={{ color }}>{verdictLabel}</h2>
        <p className="text-sm text-base-muted leading-relaxed mt-2 max-w-2xl">{verdict}</p>
      </div>
    </div>
  )
}
