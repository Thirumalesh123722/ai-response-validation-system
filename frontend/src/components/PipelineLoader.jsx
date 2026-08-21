const STAGES = ['Retrieving reference context', 'Relevance Judge', 'Accuracy Judge', 'Hallucination Detector', 'Completeness Judge', 'Verdict Agent']
export default function PipelineLoader() {
  return (
    <div className="rounded-lg border border-base-border card-surface p-8 flex flex-col items-center gap-6">
      <div className="w-10 h-10 rounded-full border-2 border-base-border border-t-signal-teal animate-sweep" />
      <div className="flex flex-col gap-1.5 items-center">
        <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase">Pipeline Running</p>
        <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 max-w-md">
          {STAGES.map((stage) => (<span key={stage} className="text-xs text-base-muted font-mono">{stage}</span>))}
        </div>
      </div>
    </div>
  )
}
