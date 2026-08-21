import Gauge from './Gauge'
export default function ScoreCard({ eyebrow, label, score, reasoning, flags, accent }) {
  return (
    <div className="rounded-lg border border-base-border card-surface p-5 flex flex-col gap-4 h-full">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase">{eyebrow}</p>
          <h3 className="font-display text-lg font-medium mt-0.5">{label}</h3>
        </div>
        <Gauge score={score} size={92} strokeWidth={8} accent={accent} />
      </div>
      <p className="text-sm text-base-muted leading-relaxed">{reasoning}</p>
      {flags && flags.length > 0 && (
        <div className="border-t border-base-border pt-3">
          <p className="font-mono text-[10px] tracking-widest text-signal-red uppercase mb-2">Flagged claims — {flags.length}</p>
          <ul className="space-y-1.5">
            {flags.map((flag, i) => (<li key={i} className="text-xs text-base-text/90 flex gap-2"><span className="text-signal-red mt-0.5">▲</span><span>{flag}</span></li>))}
          </ul>
        </div>
      )}
    </div>
  )
}
