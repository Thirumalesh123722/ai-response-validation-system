export default function SubmissionSummary({ question, aiResponse }) {
  return (
    <div className="rounded-lg border border-base-border card-surface p-5">
      <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-3">Submission Reviewed</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <p className="text-[10px] font-mono text-base-muted uppercase tracking-widest mb-1">Question</p>
          <p className="text-sm text-base-text leading-relaxed">{question}</p>
        </div>
        <div>
          <p className="text-[10px] font-mono text-base-muted uppercase tracking-widest mb-1">AI Response</p>
          <p className="text-sm text-base-text leading-relaxed">{aiResponse}</p>
        </div>
      </div>
    </div>
  )
}
