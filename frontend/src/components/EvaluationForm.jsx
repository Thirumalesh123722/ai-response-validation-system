import { useState } from 'react'
import { ingestDocument } from '../lib/api'

export default function EvaluationForm({ onSubmit, isLoading }) {
  const [question, setQuestion] = useState('')
  const [aiResponse, setAiResponse] = useState('')
  const [referenceAnswer, setReferenceAnswer] = useState('')
  const [systemName, setSystemName] = useState('')
  const [sourceDocumentId, setSourceDocumentId] = useState(null)
  const [sourceFileName, setSourceFileName] = useState('')
  const [uploadStatus, setUploadStatus] = useState('idle')

  const handleFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadStatus('uploading')
    setSourceFileName(file.name)
    try {
      const res = await ingestDocument(file)
      setSourceDocumentId(res.document_id)
      setUploadStatus('done')
    } catch {
      setUploadStatus('error')
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      question,
      ai_response: aiResponse,
      reference_answer: referenceAnswer || null,
      source_document_id: sourceDocumentId,
      system_name: systemName.trim() || 'Unspecified',
    })
  }

  const canSubmit = question.trim() && aiResponse.trim() && !isLoading

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div>
        <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">
          AI system name <span className="text-base-muted/60 normal-case">(optional — e.g. "ChatGPT", "System A")</span>
        </label>
        <input
          type="text" value={systemName} onChange={(e) => setSystemName(e.target.value)} placeholder="Unspecified"
          className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2 text-sm text-base-text placeholder:text-base-muted/60 focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue"
        />
      </div>

      <div>
        <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">Question</label>
        <textarea
          value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} placeholder="What was actually asked?"
          className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2.5 text-sm text-base-text placeholder:text-base-muted/60 focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue resize-none"
        />
      </div>

      <div>
        <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">AI Response to evaluate</label>
        <textarea
          value={aiResponse} onChange={(e) => setAiResponse(e.target.value)} rows={6} placeholder="Paste the AI-generated answer here."
          className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2.5 text-sm text-base-text placeholder:text-base-muted/60 focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue resize-none"
        />
      </div>

      <div>
        <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">
          Reference answer <span className="text-base-muted/60 normal-case">(optional)</span>
        </label>
        <textarea
          value={referenceAnswer} onChange={(e) => setReferenceAnswer(e.target.value)} rows={3} placeholder="Ground truth to check against, if you have one."
          className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2.5 text-sm text-base-text placeholder:text-base-muted/60 focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue resize-none"
        />
      </div>

      <div>
        <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">
          Source document <span className="text-base-muted/60 normal-case">(optional — feeds the RAG knowledge base)</span>
        </label>
        <div className="mt-2 flex items-center gap-3">
          <label className="cursor-pointer rounded-md border border-dashed border-base-border px-3 py-2 text-xs text-base-muted hover:border-signal-blue hover:text-base-text transition-colors">
            <input type="file" accept=".pdf,.txt,.md" onChange={handleFile} className="hidden" />
            Choose file
          </label>
          {sourceFileName && (
            <span className="text-xs font-mono text-base-muted truncate max-w-[220px]">
              {sourceFileName}{' '}
              {uploadStatus === 'uploading' && <span className="text-signal-amber">indexing…</span>}
              {uploadStatus === 'done' && <span className="text-signal-teal">indexed ✓</span>}
              {uploadStatus === 'error' && <span className="text-signal-red">failed</span>}
            </span>
          )}
        </div>
      </div>

      <button
        type="submit" disabled={!canSubmit}
        className="mt-2 rounded-md bg-signal-blue disabled:bg-base-border disabled:text-base-muted disabled:cursor-not-allowed text-base-bg font-display font-semibold text-sm py-3 hover:brightness-110 transition-all"
      >
        {isLoading ? 'Running evaluation…' : 'Run Evaluation'}
      </button>
    </form>
  )
}
